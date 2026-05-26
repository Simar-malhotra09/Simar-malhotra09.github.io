#!/usr/bin/env python3
"""
build.py – Convert main.md journal entries into index.html
Run:  python3 build.py
"""

import re, sys, subprocess, tempfile
from pathlib import Path

DIR = Path(__file__).resolve().parent

# Width of the column that typst-rendered pages live in.  Bigger value = SVGs
# render larger by default.  Each .typst-page SVG fills 100% of this column.
TYPST_PAGE_WIDTH = 900

MONTHS = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# ── inline markdown ────────────────────────────────────────────────


def md_inline(text):
    """Bold, italic, code, links.  Rewrites .md hrefs → .html."""

    def _link(m):
        href = m.group(2)
        if href.endswith(".md") or href.endswith(".typ"):
            href = re.sub(r"\.(md|typ)$", ".html", href)
        return f'<a href="{href}">{m.group(1)}</a>'

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img alt="\1" src="\2">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


# ── journal parser ─────────────────────────────────────────────────


def parse_journal(path):
    """Parse main.md into dated entries and `## @Name` pinned sections."""
    text = path.read_text()
    entries, sections = [], []
    kind, key, buf = None, None, []
    for line in text.splitlines():
        dm = re.match(r"^##\s+(\d{4}/\d{1,2}/\d{1,2})", line)
        sm = re.match(r"^##\s+@(.+)$", line)
        if dm or sm:
            if kind == "entry":
                entries.append((key, buf))
            elif kind == "section":
                sections.append((key, buf))
            if dm:
                kind, key, buf = "entry", dm.group(1), []
            else:
                kind, key, buf = "section", sm.group(1).strip(), []
        elif kind is not None:
            buf.append(line)
    if kind == "entry":
        entries.append((key, buf))
    elif kind == "section":
        sections.append((key, buf))
    return entries, sections

def join_escaped_newlines(lines):
    out = []
    for line in lines:
        if out and out[-1].rstrip().endswith("\\"):
            out[-1] = out[-1].rstrip()[:-1] + "<br>" + line.lstrip()
        else:
            out.append(line)
    return out

def render_items(lines):
    """Markdown list lines → HTML <li>s (one level of nesting)."""
    lines = join_escaped_newlines(lines) 
    out, i = [], 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        m = re.match(r"^- (.+)$", lines[i])
        if not m:
            i += 1
            continue
        content = md_inline(m.group(1))
        subs, j = [], i + 1
        while j < len(lines):
            sm = re.match(r"^ +- (.+)$", lines[j])
            if sm:
                subs.append(md_inline(sm.group(1)))
                j += 1
            elif not lines[j].strip():
                j += 1
            else:
                break
        if subs:
            out.append("        <li>")
            out.append(f"          {content}")
            out.append("          <ul>")
            for s in subs:
                out.append(f"            <li>{s}</li>")
            out.append("          </ul>")
            out.append("        </li>")
        else:
            out.append(f"        <li>{content}</li>")
        i = j
    return "\n".join(out)


# ── sub-page converter ─────────────────────────────────────────────

SUBPAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    body {{ font-family: monospace; max-width: 600px; margin: 40px auto; padding: 0 20px; }}
    a {{ color: #0057b7; }}
    pre {{ background: #f5f5f5; padding: 12px; overflow-x: auto; }}
    ul {{ margin: 8px 0 16px 20px; }}
    li {{ margin: 4px 0; }}
    img {{ max-width: 100%; height: auto; display: block; margin: 16px auto; }}
  </style>
</head>
<body>
  <p><a href="index.html">&larr; back</a></p>
  <main>
    {body}
  </main>
</body>
</html>
"""


def convert_subpage(md_path):
    """Convert a standalone .md file to .html."""
    text = md_path.read_text()
    lines = join_escaped_newlines(text.splitlines())
    body, in_ul = [], False
    for line in lines:
        hm = re.match(r"^(#{1,6})\s+(.+)$", line)
        lm = re.match(r"^(\s*)- (.+)$", line)
        if hm:
            if in_ul:
                body.append("</ul>")
                in_ul = False
            n = len(hm.group(1))
            body.append(f"<h{n}>{md_inline(hm.group(2))}</h{n}>")
        elif lm:
            if not in_ul:
                body.append("<ul>")
                in_ul = True
            body.append(f"<li>{md_inline(lm.group(2))}</li>")
        elif not line.strip():
            if in_ul:
                body.append("</ul>")
                in_ul = False
        else:
            if in_ul:
                body.append("</ul>")
                in_ul = False
            body.append(f"<p>{md_inline(line)}</p>")
    if in_ul:
        body.append("</ul>")

    title = md_path.stem.replace("-", " ").replace("_", " ").title()
    tm = re.search(r"^#\s+(.+)$", text, re.M)
    if tm:
        title = tm.group(1)

    html_out = md_path.with_suffix(".html")
    html_out.write_text(
        SUBPAGE_TEMPLATE.format(
            title=title,
            body="\n    ".join(body),
        )
    )
    print(f"  -> {html_out.relative_to(DIR)}")


# ── typst converter ────────────────────────────────────────────────

TYPST_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    body {{ font-family: monospace; max-width: {width}px; margin: 40px auto; padding: 0 20px; }}
    a {{ color: #0057b7; }}
    .typst-page svg {{ max-width: 100%; height: auto; display: block; margin: 0 auto; }}
    .typst-page + .typst-page {{ margin-top: 24px; border-top: 1px solid #eee; padding-top: 24px; }}
  </style>
</head>
<body>
  <p><a href="index.html">&larr; back</a></p>
  <main>
    {body}
  </main>
</body>
</html>
"""


def convert_typst(typ_path):
    """Compile a .typ file via `typst compile`, embed each page as inline SVG."""
    title = typ_path.stem.replace("-", " ").replace("_", " ").title()
    with tempfile.TemporaryDirectory() as tmp:
        pattern = str(Path(tmp) / f"{typ_path.stem}-{{n}}.svg")
        try:
            subprocess.run(
                ["typst", "compile", str(typ_path), pattern],
                check=True,
                capture_output=True,
            )
        except FileNotFoundError:
            print(f"  error: `typst` not on PATH; skipping {typ_path.name}", file=sys.stderr)
            return
        except subprocess.CalledProcessError as e:
            print(
                f"  error: typst failed for {typ_path.name}:\n{e.stderr.decode().strip()}",
                file=sys.stderr,
            )
            return

        svgs = sorted(
            Path(tmp).glob(f"{typ_path.stem}-*.svg"),
            key=lambda p: int(re.search(r"-(\d+)\.svg$", p.name).group(1)),
        )
        pages = []
        for svg in svgs:
            content = re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", svg.read_text())
            pages.append(f'<div class="typst-page">{content}</div>')

    html_out = typ_path.with_suffix(".html")
    html_out.write_text(
        TYPST_TEMPLATE.format(
            title=title,
            body="\n    ".join(pages),
            width=TYPST_PAGE_WIDTH,
        )
    )
    print(f"  -> {html_out.relative_to(DIR)} ({len(pages)} pages)")


# ── main builder ───────────────────────────────────────────────────

INDEX_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>0saker</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: monospace; min-height: 100vh; }}
    nav {{
      width: 120px;
      padding: 12px;
      border-left: 1px solid #eee;
      position: fixed;
      top: 0; right: 0; bottom: 0;
      overflow-y: auto;
    }}
    nav ul {{ list-style: none; }}
    nav li {{ margin: 1px 0; }}
    nav a {{ color: #999; text-decoration: none; font-size: 11px; }}
    nav a:hover {{ text-decoration: underline; }}
    nav li.nav-head {{
      font-size: 10px;
      color: #bbb;
      letter-spacing: 0.5px;
      margin-top: 8px;
      margin-bottom: 2px;
    }}
    nav li.nav-head:first-child {{ margin-top: 0; }}
    main {{
      max-width: 600px;
      padding: 10px 20px;
      margin-left: 30px;
    }}
    main h3 {{ margin-top: 24px; scroll-margin-top: 20px; }}
    main ul {{ margin: 8px 0 16px 20px; }}
    main li {{ margin: 4px 0; }}
    main img {{ max-width: 100%; height: auto; }}
    aside.pinned {{
      position: fixed;
      top: 12px;
      left: calc(40% + 5px);
      width: 300px;
      padding: 12px;
      overflow: hidden;
    }}
    aside.pinned h4 {{
      font-size: 11px;
      margin-top: 12px;
      margin-bottom: 4px;
      color: #888;
      font-weight: normal;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    aside.pinned h4:first-child {{ margin-top: 0; }}
    aside.pinned ul {{ list-style:disc; margin: 0 0 8px 0; padding-left: 20px; }}
    aside.pinned li {{ margin: 3px 0; font-size: 11px; line-height: 1.4; }}
    aside.pinned ul ul {{ list-style: circle; margin: 2px 0 2px 10px; padding-left:20px; }}
    a {{ color: #0057b7; }}
    @media (max-width: 1020px) {{
      aside.pinned {{
        position: static;
        width: auto;
        margin: 16px 20px 0 30px;
        padding: 0;
        border-top: 1px solid #eee;
        padding-top: 16px;
      }}
    }}
    @media (max-width: 640px) {{
      nav {{
        position: static;
        width: 100%;
        border-right: none;
        border-bottom: 1px solid #eee;
        overflow-y: visible;
        display: flex;
      }}
      nav ul {{ display: flex; flex-wrap: wrap; gap: 4px 10px; }}
      main {{ margin-left: 0; }}
      aside.pinned {{ margin-left: 0; margin-right: 0; padding: 16px 20px 0; }}
    }}
  </style>
</head>
<body>
  <nav>
    <ul>
{sidebar}
    </ul>
  </nav>
  <main>
{content}
  </main>
  <aside class="pinned">
{pinned}
  </aside>
</body>
</html>
"""


def build():
    md_file = DIR / "main.md"
    if not md_file.exists():
        print(f"error: {md_file} not found", file=sys.stderr)
        sys.exit(1)

    entries, sections = parse_journal(md_file)
    if not entries:
        print("warning: no entries found (use ## YYYY/MM/DD headers)", file=sys.stderr)

    section_anchors = [
        (re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"), name) for name, _ in sections
    ]

    # sidebar: pinned links first, then date entries
    sidebar_lines = []
    if sections:
        sidebar_lines.append('      <li class="nav-head">PINNED</li>')
        for slug, name in section_anchors:
            sidebar_lines.append(f'      <li><a href="#p-{slug}">{name}</a></li>')
        sidebar_lines.append('      <li class="nav-head">---</li>')
    for ds, _ in entries:
        y, m, d = (int(x) for x in ds.split("/"))
        anchor = f"d-{y}-{m:02d}-{d:02d}"
        label = f"{y}/{MONTHS[m]}/{d:02d}"
        sidebar_lines.append(f'      <li><a href="#{anchor}">{label}</a></li>')

    # content
    content_blocks = []
    for ds, lines in entries:
        y, m, d = (int(x) for x in ds.split("/"))
        anchor = f"d-{y}-{m:02d}-{d:02d}"
        items = render_items(lines)
        block = f'    <h3 id="{anchor}">{ds}</h3>\n    <ul>\n{items}\n    </ul>'
        content_blocks.append(block)

    # pinned sections (middle column)
    pinned_blocks = []
    for (slug, name), (_, lines) in zip(section_anchors, sections):
        items = render_items(lines)
        if items:
            pinned_blocks.append(f'    <h4 id="p-{slug}">{name}</h4>\n    <ul>\n{items}\n    </ul>')
        else:
            pinned_blocks.append(f'    <h4 id="p-{slug}">{name}</h4>')

    html = INDEX_TEMPLATE.format(
        sidebar="\n".join(sidebar_lines),
        content="\n\n".join(content_blocks),
        pinned="\n".join(pinned_blocks),
    )

    out = DIR / "index.html"
    out.write_text(html)
    print(f"index.html <- {len(entries)} entries, {len(sections)} pinned sections")

    # convert any linked .md or .typ sub-pages
    raw = md_file.read_text()
    for href in re.findall(r"\]\(([^)]+\.(?:md|typ))\)", raw):
        sub = DIR / href
        if not sub.exists():
            print(f"  warning: {href} not found, skipping", file=sys.stderr)
            continue
        if sub.suffix == ".typ":
            convert_typst(sub)
        else:
            convert_subpage(sub)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if not target.exists():
            print(f"error: {target} not found", file=sys.stderr)
            sys.exit(1)
        if target.suffix == ".typ":
            convert_typst(target)
        else:
            convert_subpage(target)
    else:
        build()
