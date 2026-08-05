#!/usr/bin/env python3
"""Render any sprite JSON to text (to LOOK at) and to PNG data URIs (to ship).

    python3 scripts/render_sprite.py data/potus-sprite.json

A hand-typed pixel grid validates fine as code while being misshapen art. This project
has already shipped a sprite with slab ears and an off-centre row that every automated
check passed. So: always render to text and actually look at it before shipping.
"""
import sys
import json
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from sprite import frame_png, data_uri, validate, to_text  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: render_sprite.py <sprite.json>")
    path = pathlib.Path(sys.argv[1]).resolve()
    d = json.loads(path.read_text(encoding="utf-8"))
    pal, frames = d["palette"], d["frames"]
    validate(pal, frames)

    size = len(next(iter(frames.values())))
    print(f"{path.name}: {size}x{size}, {len([k for k in pal if pal[k]])} colours, "
          f"frames: {', '.join(frames)}\n")

    uris = {name: data_uri(frame_png(pal, rows, scale=4)) for name, rows in frames.items()}
    out = path.with_name(path.stem.replace("-sprite", "") + "-frames.json")
    out.write_text(json.dumps(uris, indent=2), encoding="utf-8")
    for name, uri in uris.items():
        print(f"  {name:6s} -> {len(uri):,} chars base64")
    print(f"\nwrote {out.relative_to(ROOT)}\n")

    for name, rows in frames.items():
        print(f"--- {name} ---")
        print(to_text(pal, rows))
        print()


if __name__ == "__main__":
    main()
