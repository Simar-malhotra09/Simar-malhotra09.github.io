#!/usr/bin/env python3
"""
build.py – Convert main.md journal entries into index.html, and any linked
           .md / .typ sub-pages into HTML with a heading-level sidebar.
Run:  python3 build.py           # full build
      python3 build.py <file>    # build a single .md or .typ file
"""

import re, sys, subprocess, tempfile
from pathlib import Path

DIR = Path(__file__).resolve().parent

TYPST_PAGE_WIDTH = 900

MONTHS = [
    "",
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


# ── inline markdown ────────────────────────────────────────────────


def md_inline(text: str) -> str:
    """Bold, italic, code, links.  Rewrites .md / .typ hrefs → .html."""

    def _link(m: re.Match) -> str:
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


def heading_slug(raw: str) -> str:
    """Slugify a heading string, stripping markdown link syntax first."""
    plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", raw)
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")


def heading_plain(raw: str) -> str:
    """Strip all markdown syntax to get plain text for display."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", raw)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text


def back_link(html_out: Path) -> str:
    depth = len(html_out.relative_to(DIR).parts) - 1
    return "../" * depth + "index.html"


def parse_links(path: Path, prefix: str = "") -> list[tuple[str, list[str]]]:
    """Return [(section, [rendered_html, ...]), ...] from a links.md file.
    Renders each list item fully (link + description); rewrites relative hrefs with prefix."""
    sections: list[tuple[str, list[str]]] = []
    current: str | None = None
    items: list[str] = []
    lines= join_escaped_newlines(path.read_text().splitlines())
    for line in lines:
        hm = re.match(r"^##\s+(.+)$", line)
        lm = re.match(r"^- (.+)$", line)
        if hm:
            if current is not None:
                sections.append((current, items))
            current, items = hm.group(1), []
        elif lm and current is not None:
            content = lm.group(1)

            def _link(m: re.Match) -> str:
                href = m.group(2)
                if not href.startswith(("http://", "https://")):
                    href = prefix + re.sub(r"\.(md|typ)$", ".html", href)
                return f'<a href="{href}">{m.group(1)}</a>'

            html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link, content)
            html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
            html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
            items.append(html)
    if current is not None:
        sections.append((current, items))
    return sections


# ── journal parser ─────────────────────────────────────────────────


def parse_journal(path: Path) -> tuple[list, str]:
    text = path.read_text()
    entries: list = []
    intro_lines: list[str] = []
    kind: str | None = None
    key: str | None = None
    buf: list[str] = []
    in_comment = False

    for line in text.splitlines():
        if "<!--" in line:
            in_comment = True
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        dm = re.match(r"^##\s+(\d{4}/\d{1,2}/\d{1,2})", line)
        if dm:
            if kind == "entry":
                entries.append((key, buf))
            kind, key, buf = "entry", dm.group(1), []
        elif kind is None:
            intro_lines.append(line)
        else:
            buf.append(line)

    if kind == "entry":
        entries.append((key, buf))

    intro = md_inline(" ".join(l.strip() for l in intro_lines if l.strip()))
    return entries, intro


def join_escaped_newlines(lines: list) -> list:
    out = []
    for line in lines:
        if out and out[-1].rstrip().endswith("\\"):
            out[-1] = out[-1].rstrip()[:-1] + "<br>" + line.lstrip()
        else:
            out.append(line)
    return out


def render_items(lines: list) -> str:
    lines = join_escaped_newlines(lines)

    # Parse list lines into (indent_level, html_content).
    # A leading [iN] marker means "indent N levels" and is removed from output.
    # Lines that start with whitespace before the dash are kept as level 1 for
    # backwards compatibility with the old indented-sublist style.
    items: list[tuple[int, str]] = []
    for line in lines:
        if not line.strip():
            continue
        m = re.match(r"^(\s*)- (.+)$", line)
        if not m:
            continue
        spaces, content = m.group(1), m.group(2)
        im = re.match(r"^\[i(\d+)\]\s*", content)
        if im:
            level = int(im.group(1))
            content = content[im.end():]
        elif spaces:
            level = 1
        else:
            level = 0
        items.append((level, md_inline(content)))

    if not items:
        return ""

    # Build a tree from the flat (level, content) list.
    root = {"level": -1, "children": []}
    stack = [root]
    for level, content in items:
        while stack and stack[-1]["level"] >= level:
            stack.pop()
        node = {"level": level, "content": content, "children": []}
        stack[-1]["children"].append(node)
        stack.append(node)

    def render(node: dict, depth: int) -> list[str]:
        out: list[str] = []
        li_indent = " " * (8 + depth * 4)
        ul_indent = " " * (10 + depth * 4)
        for child in node["children"]:
            if child["children"]:
                out.append(f"{li_indent}<li>{child['content']}")
                out.append(f"{ul_indent}<ul>")
                out.extend(render(child, depth + 1))
                out.append(f"{ul_indent}</ul>")
                out.append(f"{li_indent}</li>")
            else:
                out.append(f"{li_indent}<li>{child['content']}</li>")
        return out

    return "\n".join(render(root, 0))


# ── sub-page converter ─────────────────────────────────────────────


SUBPAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: monospace; min-height: 100vh; }}
    nav {{
      width: 10px;
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
    nav li.nav-back {{ margin-bottom: 4px; }}
    main {{
      max-width: 600px;
      padding: 20px 20px 40px;
      margin-left: 30px;
    }}
    main h2, main h3 {{ margin-top: 24px; scroll-margin-top: 20px; }}
    main ul {{ margin: 8px 0 16px 20px; }}
    main li {{ margin: 4px 0; }}
    main img {{ max-width: 100%; height: auto; display: block; margin: 16px auto; }}
    pre {{ background: #f5f5f5; padding: 12px; overflow-x: auto; }}
    a {{ color: #0057b7; }}
    @media (max-width: 640px) {{
      nav {{
        position: static;
        width: 100%;
        border-left: none;
        border-bottom: 1px solid #eee;
        overflow-y: visible;
        display: flex;
      }}
      nav ul {{ display: flex; flex-wrap: wrap; gap: 4px 10px; }}
      main {{ margin-left: 0; }}
    }}
  </style>
</head>
<body>
  <nav>
    <ul>
      <li class="nav-back"><a href="{back}">&larr; back</a></li>
{sidebar}
    </ul>
  </nav>
  <main>
{body}
  </main>
</body>
</html>
"""


def convert_subpage(md_path: Path) -> None:
    text = md_path.read_text()
    lines = join_escaped_newlines(text.splitlines())
    body: list[str] = []
    sidebar_items: list[str] = []
    in_ul = False

    for line in lines:
        hm = re.match(r"^(#{1,6})\s+(.+)$", line)
        lm = re.match(r"^(\s*)- (.+)$", line)
        if hm:
            if in_ul:
                body.append("</ul>")
                in_ul = False
            n = len(hm.group(1))
            raw = hm.group(2)
            slug = heading_slug(raw)
            body.append(f"<h{n} id=\"{slug}\">{md_inline(raw)}</h{n}>")
            if n <= 3:
                sidebar_items.append(
                    f'      <li><a href="#{slug}">{heading_plain(raw)}</a></li>'
                )
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
    back = back_link(html_out)

    sidebar = ""
    if sidebar_items:
        sidebar = (
            '      <li class="nav-head">CONTENTS</li>\n' + "\n".join(sidebar_items)
        )

    html_out.write_text(
        SUBPAGE_TEMPLATE.format(
            title=title,
            body="\n    ".join(body),
            sidebar=sidebar,
            back=back,
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
  <p><a href="{back}">&larr; back</a></p>
  <main>
    {body}
  </main>
</body>
</html>
"""


def convert_typst(typ_path: Path) -> None:
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
            print(
                f"  error: `typst` not on PATH; skipping {typ_path.name}",
                file=sys.stderr,
            )
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
    back = back_link(html_out)
    html_out.write_text(
        TYPST_TEMPLATE.format(
            title=title,
            body="\n    ".join(pages),
            width=TYPST_PAGE_WIDTH,
            back=back,
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
      width: 180px;
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
      margin-top: 10px;
      margin-bottom: 2px;
    }}
    nav li.nav-head:first-child {{ margin-top: 0; }}
    .layout {{
      display: flex;
      align-items: flex-start;
      margin-left: 30px;
      margin-right: 200px;
    }}
    main {{
      max-width: 560px;
      padding: 20px 20px 40px 20px;
      flex: 1;
      min-width: 0;
    }}
    #intro {{ margin-bottom: 28px; line-height: 1.5; }}
    main h3 {{ margin-top: 24px; scroll-margin-top: 20px; }}
    main ul {{ margin: 8px 0 16px 20px; }}
    main li {{ margin: 4px 0; }}
    main img {{ max-width: 100%; height: auto; }}
    aside.pinned {{
      width: 280px;
      padding: 20px 0 40px 32px;
      flex-shrink: 0;
    }}
    aside.pinned .aside-head {{
      font-size: 10px;
      color: #bbb;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      margin-top: 16px;
      margin-bottom: 4px;
    }}
    aside.pinned .aside-head:first-child {{ margin-top: 0; }}
    aside.pinned ul {{ list-style: none; }}
    aside.pinned li {{ margin: 2px 0; }}
    aside.pinned a {{ color: #999; text-decoration: none; font-size: 11px; }}
    aside.pinned a:hover {{ text-decoration: underline; }}
    a {{ color: #0057b7; }}
    @media (max-width: 1020px) {{
      .layout {{ flex-direction: column; margin-right: 200px; }}
      aside.pinned {{
        width: auto;
        padding: 16px 20px 40px 20px;
        border-top: 1px solid #eee;
      }}
    }}
    @media (max-width: 640px) {{
      nav {{
        position: static;
        width: 100%;
        border-left: none;
        border-bottom: 1px solid #eee;
        overflow-y: visible;
        display: flex;
      }}
      nav ul {{ display: flex; flex-wrap: wrap; gap: 4px 10px; }}
      .layout {{ margin-left: 0; margin-right: 0; }}
    }}
  </style>
</head>
<body>
  <nav>
    <ul>
{sidebar}
    </ul>
  </nav>
  <div class="layout">
    <main>
      <p id="intro">{intro}</p>
{content}
    </main>
    <aside class="pinned">
{aside}
    </aside>
  </div>
</body>
</html>
"""


def build() -> None:
    md_file = DIR / "main.md"
    if not md_file.exists():
        print(f"error: {md_file} not found", file=sys.stderr)
        sys.exit(1)

    entries, intro = parse_journal(md_file)
    if not entries:
        print("warning: no entries found (use ## YYYY/MM/DD headers)", file=sys.stderr)

    sidebar_lines = [
        '      <li class="nav-head">LOG</li>',
    ]
    for ds, _ in entries:
        y, m, d = (int(x) for x in ds.split("/"))
        anchor = f"d-{y}-{m:02d}-{d:02d}"
        label = f"{y}/{MONTHS[m]}/{d:02d}"
        sidebar_lines.append(f'      <li><a href="#{anchor}">{label}</a></li>')

    content_blocks = []
    for ds, lines in entries:
        y, m, d = (int(x) for x in ds.split("/"))
        anchor = f"d-{y}-{m:02d}-{d:02d}"
        items = render_items(lines)
        block = f'    <h3 id="{anchor}">{ds}</h3>\n    <ul>\n{items}\n    </ul>'
        content_blocks.append(block)

    aside_lines: list[str] = []
    links_md = DIR / "writing" / "links.md"
    if links_md.exists():
        for section, items in parse_links(links_md, prefix="writing/"):
            aside_lines.append(f'      <p class="aside-head">{section}</p>')
            if items:
                aside_lines.append('      <ul>')
                for item_html in items:
                    aside_lines.append(f'        <li>{item_html}</li>')
                aside_lines.append('      </ul>')

    html = INDEX_TEMPLATE.format(
        sidebar="\n".join(sidebar_lines),
        intro=intro,
        content="\n\n".join(content_blocks),
        aside="\n".join(aside_lines),
    )

    out = DIR / "index.html"
    out.write_text(html)
    print(f"index.html <- {len(entries)} entries")

    built: set[Path] = set()

    def build_file(path: Path) -> None:
        path = path.resolve()
        if path in built:
            return
        built.add(path)
        if path.suffix == ".typ":
            convert_typst(path)
            return
        convert_subpage(path)
        for href in re.findall(r"\]\(([^)]+\.(?:md|typ))\)", path.read_text()):
            child = (path.parent / href).resolve()
            if child.exists():
                build_file(child)

    for href in re.findall(r"\]\(([^)]+\.(?:md|typ))\)", md_file.read_text()):
        sub = (DIR / href).resolve()
        if sub.exists():
            build_file(sub)

    for entry_point in [DIR / "writing" / "links.md", DIR / "writing" / "int.md"]:
        if entry_point.exists():
            build_file(entry_point)


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
