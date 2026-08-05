#!/usr/bin/env python3
"""Wrap the artifact fragment (dashboard.html) into complete, distributable HTML documents.

The artifact build deliberately omits <!DOCTYPE>/<html>/<head>/<body> because Claude
injects them at publish time. A real web server does not, and without a doctype every
browser drops into quirks mode.

Two outputs, because there are two ways this page reaches a person:

  docs/index.html        hosted build — links to icon/manifest files next to it, so an
                         iPad can Add to Home Screen and get a real app icon.

  Market Recap.html      sendable build — ONE file, zero external references, icon inlined
                         as a data URI. AirDrop it, text it, email it. The recipient taps
                         it and it opens. No account, no login, no internet needed.
"""
import re
import base64
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "dashboard.html"
OUT = ROOT / "docs" / "index.html"
OUT_STANDALONE = ROOT / "Market Recap.html"


def split_head_body(fragment: str):
    """Everything through the last </style> belongs in <head>; the rest is <body>."""
    idx = fragment.rfind("</style>")
    if idx == -1:
        raise SystemExit("wrap_site: no </style> found — fragment structure changed")
    cut = idx + len("</style>")
    return fragment[:cut], fragment[cut:]


def strip_from_head(head: str):
    """Pull charset/viewport/title out of the fragment head; we re-emit them ourselves
    so we control their order and can add the app tags alongside."""
    title = "Morning Market Recap"
    m = re.search(r"<title>(.*?)</title>", head, re.S)
    if m:
        title = m.group(1).strip()
    head = re.sub(r'<meta\s+charset=[^>]*>\s*', "", head, flags=re.I)
    head = re.sub(r'<meta\s+name="viewport"[^>]*>\s*', "", head, flags=re.I)
    head = re.sub(r"<title>.*?</title>\s*", "", head, flags=re.S | re.I)
    return head, title


DESC = ("A plain-English morning recap of five positions: the S&amp;P 500, the Nasdaq 100, "
        "Nvidia, SOXL and Costco. What moved, what it means, and what to watch next.")


def build(fragment: str, standalone: bool) -> str:
    head, body = split_head_body(fragment)
    head, title = strip_from_head(head)

    if standalone:
        # Inline the icon so the file has no external references whatsoever. A page sent
        # over AirDrop or email has no server next to it to fetch anything from.
        icon_path = ROOT / "docs" / "icon-180.png"
        icon_uri = ""
        if icon_path.exists():
            b64 = base64.b64encode(icon_path.read_bytes()).decode("ascii")
            icon_uri = f"data:image/png;base64,{b64}"
        icon_tags = (f'<link rel="apple-touch-icon" href="{icon_uri}">\n'
                     f'<link rel="icon" type="image/png" href="{icon_uri}">') if icon_uri else ""
    else:
        icon_tags = ('<link rel="apple-touch-icon" href="icon-180.png">\n'
                     '<link rel="icon" type="image/png" href="icon-180.png">\n'
                     '<link rel="manifest" href="manifest.webmanifest">')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{DESC}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#F7F8F9" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0C1116" media="(prefers-color-scheme: dark)">

<!-- Add to Home Screen on iPad/iPhone: opens chrome-free, like an app -->
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Market Recap">
{icon_tags}

<!-- Link preview when this gets texted or emailed to someone -->
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{DESC}">
<meta name="twitter:card" content="summary">
{head}
</head>
<body>
{body}
</body>
</html>
"""


def main():
    if not SRC.exists():
        raise SystemExit(f"wrap_site: {SRC} not found")
    fragment = SRC.read_text(encoding="utf-8")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(fragment, standalone=False), encoding="utf-8")
    print(f"wrap_site: wrote {OUT} ({OUT.stat().st_size:,} bytes)")

    OUT_STANDALONE.write_text(build(fragment, standalone=True), encoding="utf-8")
    print(f"wrap_site: wrote {OUT_STANDALONE} ({OUT_STANDALONE.stat().st_size:,} bytes)")

    # A sendable file that FETCHES something at load time is a broken sendable file.
    # Anchor hrefs are fine — those are source citations the reader taps on purpose, and
    # they cost nothing when offline. What must not exist is any SUBRESOURCE: anything the
    # browser goes and gets by itself while rendering.
    text = OUT_STANDALONE.read_text(encoding="utf-8")
    bad = []
    bad += re.findall(r'<(?:img|script|iframe|source|video|audio)\b[^>]*\bsrc="(?!data:)([^"]+)"', text, re.I)
    bad += re.findall(r'<link\b[^>]*\bhref="(?!data:)([^"]+)"', text, re.I)
    bad += re.findall(r'url\(\s*["\']?(?!data:|#)([^)"\']+)', text, re.I)
    bad += re.findall(r'@import\s+["\']([^"\']+)', text, re.I)
    if bad:
        raise SystemExit(f"wrap_site: standalone fetches external subresources: {sorted(set(bad))[:5]}")

    links = len(re.findall(r'<a\b[^>]*\bhref="https?://', text, re.I))
    print(f"wrap_site: standalone verified — 0 subresources, {links} source links (tap-only, fine offline)")


if __name__ == "__main__":
    main()
