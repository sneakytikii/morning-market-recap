#!/usr/bin/env python3
"""Pancho's sprite: one source of truth, rendered to PNG data URIs and app icons.

WHY THIS EXISTS — the iPad bug:

Pancho used to be drawn to three <canvas> elements by JavaScript, once, at page load. On
the iPad he did not appear at all. Three separate causes stack up:

  1. iOS Safari purges canvas backing stores under memory pressure. The page drew each
     canvas exactly once and had no repaint path, so a purge was permanent.
  2. The only thing that ever redrew was the blink timer, which begins
     `if (mq.matches || wagging) return;` — so with Reduce Motion switched on, the redraw
     could never happen. That setting is likely on for the 65-year-old reader this page
     is built for.
  3. `filter: drop-shadow()` plus `animation` on a <canvas> is a known iOS compositing
     bug that renders the element blank.

Rendering the frames to PNG data URIs at build time and using <img> removes the whole
class of failure: an <img> is never purged, never depends on a timer, never depends on
JavaScript running at all, and survives every compositing path. Animation becomes a `src`
swap between frames that are already in memory.

Costs about 2.5KB of base64 for three frames. Worth it.
"""
import re
import json
import zlib
import base64
import struct
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "dashboard.html"
SPRITE_JSON = ROOT / "data" / "pancho-sprite.json"
SITE = ROOT / "docs"


# ---------------------------------------------------------------- PNG encoding

def png_bytes(width, height, rows):
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def hex_rgb(h):
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))


def frame_png(pal, rows, scale=1, bg=None, pad=0):
    """Render one frame. bg=None gives a transparent background."""
    gh, gw = len(rows), max(len(r) for r in rows)
    W, H = (gw + pad * 2) * scale, (gh + pad * 2) * scale
    bg_rgba = (*hex_rgb(bg), 255) if bg else (0, 0, 0, 0)

    out = []
    for py in range(H):
        row = bytearray()
        gy = py // scale - pad
        for px in range(W):
            gx = px // scale - pad
            rgba = bg_rgba
            if 0 <= gy < gh and 0 <= gx < len(rows[gy]):
                hexv = pal.get(rows[gy][gx])
                if hexv:
                    rgba = (*hex_rgb(hexv), 255)
            row += bytes(rgba)
        out.append(row)
    return png_bytes(W, H, out)


def data_uri(png):
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


# ---------------------------------------------------------------- extraction

def js_string_list(block):
    return re.findall(r'"([^"]*)"', block)


def extract_from_html(html):
    """Recover PAL and the three frames from the page's existing JavaScript, including
    the `WAG[20] = "..."` style row overrides."""
    pal_m = re.search(r"var PAL\s*=\s*\{(.*?)\}\s*;", html, re.S)
    if not pal_m:
        raise SystemExit("sprite: PAL not found")
    pal = {}
    for key, val in re.findall(r'"(.)"\s*:\s*(null|"#[0-9A-Fa-f]{6}")', pal_m.group(1)):
        pal[key] = None if val == "null" else val.strip('"')

    idle_m = re.search(r"var IDLE\s*=\s*\[(.*?)\]\s*;", html, re.S)
    if not idle_m:
        raise SystemExit("sprite: IDLE not found")
    idle = js_string_list(idle_m.group(1))

    frames = {"idle": idle}
    for name in ("BLINK", "WAG"):
        rows = list(idle)
        for idx, val in re.findall(rf'{name}\[(\d+)\]\s*=\s*"([^"]*)"', html):
            rows[int(idx)] = val
        frames[name.lower()] = rows

    return pal, frames


def validate(pal, frames):
    problems = []
    for name, rows in frames.items():
        widths = {len(r) for r in rows}
        if len(widths) != 1:
            problems.append(f"{name}: ragged rows {sorted(widths)}")
        if len(rows) != next(iter(widths), 0):
            problems.append(f"{name}: not square — {len(rows)} rows x {widths}")
        for y, r in enumerate(rows):
            for ch in r:
                if ch not in pal:
                    problems.append(f"{name} row {y}: char {ch!r} not in palette")
    if problems:
        raise SystemExit("sprite validation failed:\n  - " + "\n  - ".join(problems))


def to_text(pal, rows):
    """Render a frame as text blocks so a human can actually LOOK at the sprite before it
    ships. A hand-typed pixel grid validates fine as code while being misshapen art."""
    out = []
    for r in rows:
        out.append("".join("  " if pal.get(c) is None else "██" for c in r))
    return "\n".join(out)


# ---------------------------------------------------------------- main

def load():
    """data/pancho-sprite.json is the source of truth once it exists. Before that — the
    first run — recover the grids from the JavaScript still embedded in the page."""
    if SPRITE_JSON.exists():
        d = json.loads(SPRITE_JSON.read_text(encoding="utf-8"))
        return d["palette"], d["frames"]
    return extract_from_html(SRC.read_text(encoding="utf-8"))


def main():
    pal, frames = load()
    validate(pal, frames)

    size = len(frames["idle"])
    print(f"sprite: {size}x{size}, {len(pal)} palette keys, frames: {', '.join(frames)}")

    SPRITE_JSON.parent.mkdir(parents=True, exist_ok=True)
    SPRITE_JSON.write_text(json.dumps({"palette": pal, "frames": frames}, indent=2), encoding="utf-8")
    print(f"sprite: wrote {SPRITE_JSON.relative_to(ROOT)}")

    uris = {}
    for name, rows in frames.items():
        # 4x backing store: crisp at every display size, still tiny as base64.
        png = frame_png(pal, rows, scale=4)
        uris[name] = data_uri(png)
        print(f"sprite:   {name:6s} {len(png):5,}B png -> {len(uris[name]):6,} chars base64")

    (ROOT / "data" / "pancho-frames.json").write_text(json.dumps(uris, indent=2), encoding="utf-8")

    SITE.mkdir(exist_ok=True)
    for icon in (180, 192, 512):
        scale = icon // (size + 4)
        png = frame_png(pal, frames["idle"], scale=scale, bg="#FBEEDA", pad=2)
        (SITE / f"icon-{icon}.png").write_bytes(png)
    print(f"sprite: wrote {SITE.relative_to(ROOT)}/icon-{{180,192,512}}.png")

    print("\nIDLE frame — look at it before shipping:\n")
    print(to_text(pal, frames["idle"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
