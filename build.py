#!/usr/bin/env python3
"""
build.py – Convert main.md journal entries into index.html
Run:  python3 build.py
"""

import re, sys
from pathlib import Path

DIR = Path(__file__).resolve().parent

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
        if href.endswith(".md"):
            href = href[:-3] + ".html"
        return f'<a href="{href}">{m.group(1)}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


# ── journal parser ─────────────────────────────────────────────────


def parse_journal(path):
    """Return [(date_str, [raw_lines]), ...] from ## YYYY/MM/DD headers."""
    text = path.read_text()
    entries, cur, buf = [], None, []
    for line in text.splitlines():
        m = re.match(r"^##\s+(\d{4}/\d{1,2}/\d{1,2})", line)
        if m:
            if cur:
                entries.append((cur, buf))
            cur, buf = m.group(1), []
        elif cur is not None:
            buf.append(line)
    if cur:
        entries.append((cur, buf))
    return entries


def render_items(lines):
    """Markdown list lines → HTML <li>s (one level of nesting)."""
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
    body, in_ul = [], False
    for line in text.splitlines():
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
    main {{
      max-width: 600px;
      padding: 10px 20px;
      margin-left: 30px;
    }}
    main h3 {{ margin-top: 24px; scroll-margin-top: 20px; }}
    main ul {{ margin: 8px 0 16px 20px; }}
    main li {{ margin: 4px 0; }}
    a {{ color: #0057b7; }}
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
</body>
</html>
"""


def build():
    md_file = DIR / "main.md"
    if not md_file.exists():
        print(f"error: {md_file} not found", file=sys.stderr)
        sys.exit(1)

    entries = parse_journal(md_file)
    if not entries:
        print("warning: no entries found (use ## YYYY/MM/DD headers)", file=sys.stderr)

    # sidebar
    sidebar_lines = []
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

    html = INDEX_TEMPLATE.format(
        sidebar="\n".join(sidebar_lines),
        content="\n\n".join(content_blocks),
    )

    out = DIR / "index.html"
    out.write_text(html)
    print(f"index.html <- {len(entries)} entries")

    # convert any linked .md sub-pages
    raw = md_file.read_text()
    for href in re.findall(r"\]\(([^)]+\.md)\)", raw):
        sub = DIR / href
        if sub.exists():
            convert_subpage(sub)
        else:
            print(f"  warning: {href} not found, skipping", file=sys.stderr)


if __name__ == "__main__":
    build()
