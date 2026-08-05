#!/usr/bin/env python3
"""Export Pancho as a shareable pack: transparent PNGs, a spritesheet, and a showcase page.

    python3 scripts/export_pancho.py

Everything lands in pancho-pack/. The showcase is one self-contained HTML file with the
frames inlined as data URIs, so it can be AirDropped or emailed and just opens.
"""
import json
import shutil
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from sprite import frame_png, data_uri, validate, to_text  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "pancho-sprite.json"
OUT = ROOT / "pancho-pack"

# 1x is the true art; the rest are integer multiples so the pixels stay square.
SCALES = (1, 4, 8, 16)


def sheet_png(pal, frames, order, scale):
    """Horizontal spritesheet, one frame per cell, transparent background."""
    rows = [frames[k] for k in order]
    h = len(rows[0])
    w = max(len(r) for r in rows[0])
    W, H = w * len(rows) * scale, h * scale

    def hex_rgb(x):
        return (int(x[1:3], 16), int(x[3:5], 16), int(x[5:7], 16))

    out = []
    for py in range(H):
        line = bytearray()
        gy = py // scale
        for px in range(W):
            cell = px // (w * scale)
            gx = (px - cell * w * scale) // scale
            rgba = (0, 0, 0, 0)
            grid = rows[cell]
            if 0 <= gy < len(grid) and 0 <= gx < len(grid[gy]):
                hexv = pal.get(grid[gy][gx])
                if hexv:
                    rgba = (*hex_rgb(hexv), 255)
            line += bytes(rgba)
        out.append(line)
    from sprite import png_bytes
    return png_bytes(W, H, out)


SHOWCASE = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pancho Bot</title>
<style>
  :root {{
    --bg:#12161b; --card:#1a1f26; --ink:#f2f5f8; --ink-2:#aeb8c4; --rule:#2b323b;
    --accent:#E9B872;
    color-scheme: dark;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; padding:48px 24px 72px; background:var(--bg); color:var(--ink);
    font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
    display:flex; flex-direction:column; align-items:center; gap:40px;
  }}
  h1 {{ margin:0; font-size:34px; letter-spacing:-.02em; font-weight:650; }}
  .sub {{ margin:0; color:var(--ink-2); max-width:34em; text-align:center; }}
  .stage {{
    background:var(--card); border:1px solid var(--rule); border-radius:14px;
    padding:36px 48px; display:flex; flex-direction:column; align-items:center; gap:18px;
  }}
  .big {{ width:288px; height:288px; image-rendering:pixelated; display:block; }}
  .cap {{ font-size:13px; letter-spacing:.14em; text-transform:uppercase; color:var(--accent); font-weight:700; }}
  .row {{ display:flex; flex-wrap:wrap; gap:22px; justify-content:center; }}
  .cell {{
    background:var(--card); border:1px solid var(--rule); border-radius:12px;
    padding:20px 22px 16px; display:flex; flex-direction:column; align-items:center; gap:10px;
  }}
  .cell img {{ width:112px; height:112px; image-rendering:pixelated; display:block; }}
  .cell span {{ font-size:12.5px; letter-spacing:.1em; text-transform:uppercase; color:var(--ink-2); font-weight:700; }}
  .controls {{ display:flex; gap:10px; }}
  button {{
    font:inherit; font-weight:650; font-size:15px; padding:10px 18px; border-radius:8px;
    border:1px solid var(--rule); background:#222933; color:var(--ink); cursor:pointer;
  }}
  button:hover {{ border-color:var(--accent); color:var(--accent); }}
  button:focus-visible {{ outline:3px solid var(--accent); outline-offset:2px; }}
  .meta {{ color:var(--ink-2); font-size:14.5px; text-align:center; max-width:38em; }}
  code {{ background:#222933; padding:2px 6px; border-radius:4px; font-size:13px; }}
  @media (prefers-reduced-motion: reduce) {{ .big {{ animation:none !important; }} }}
</style>

<h1>Pancho Bot</h1>
<p class="sub">A 28&times;28 pixel dog, drawn after a real apricot goldendoodle — cream beard,
dark nose, teal VOYAGER harness. Three frames: resting, blinking, tail wagging.</p>

<div class="stage">
  <img class="big" id="stage" src="{idle}" alt="Pancho, animated">
  <div class="cap" id="label">idle</div>
  <div class="controls">
    <button type="button" id="play">Wag his tail</button>
    <button type="button" id="blink">Blink</button>
  </div>
</div>

<div class="row">
  <div class="cell"><img src="{idle}" alt="Pancho resting"><span>idle</span></div>
  <div class="cell"><img src="{blink}" alt="Pancho blinking"><span>blink</span></div>
  <div class="cell"><img src="{wag}" alt="Pancho with his tail up"><span>wag</span></div>
</div>

<p class="meta">Each frame is a 28-row grid of characters mapped to a colour palette, so the
whole design is <code>pancho-sprite.json</code> — 14 colours and three grids. The PNGs here
were rendered from it. Edit a character, re-render, and the art changes.</p>

<script>
  var F = {{ idle: "{idle}", blink: "{blink}", wag: "{wag}" }};
  var stage = document.getElementById("stage");
  var label = document.getElementById("label");
  var mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  var timer = null;

  function show(name) {{ stage.src = F[name]; label.textContent = name; }}

  document.getElementById("play").addEventListener("click", function () {{
    clearInterval(timer);
    if (mq.matches) {{ show("wag"); return; }}
    var n = 0;
    timer = setInterval(function () {{
      show(n % 2 === 0 ? "wag" : "idle");
      if (++n >= 8) {{ clearInterval(timer); show("idle"); }}
    }}, 140);
  }});

  document.getElementById("blink").addEventListener("click", function () {{
    clearInterval(timer);
    show("blink");
    setTimeout(function () {{ show("idle"); }}, 160);
  }});

  // Idle: blink on his own every few seconds, unless reduced motion is on.
  setInterval(function () {{
    if (mq.matches || timer) return;
    show("blink");
    setTimeout(function () {{ show("idle"); }}, 150);
  }}, 4600);
</script>
"""


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    pal, frames = d["palette"], d["frames"]
    validate(pal, frames)
    order = ["idle", "blink", "wag"]

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "png").mkdir(parents=True)

    size = len(frames["idle"])
    print("Pancho %dx%d, %d colours, frames: %s\n" % (
        size, size, len([k for k in pal if pal[k]]), ", ".join(order)))

    for name in order:
        for s in SCALES:
            png = frame_png(pal, frames[name], scale=s)
            path = OUT / "png" / ("pancho-%s@%dx.png" % (name, s))
            path.write_bytes(png)
        print("  png/pancho-%s@{1,4,8,16}x.png" % name)

    for s in (4, 8):
        (OUT / "png" / ("pancho-spritesheet@%dx.png" % s)).write_bytes(
            sheet_png(pal, frames, order, s))
    print("  png/pancho-spritesheet@{4,8}x.png  (idle | blink | wag)")

    shutil.copy2(SRC, OUT / "pancho-sprite.json")
    print("  pancho-sprite.json          the source grids + palette")

    uris = {n: data_uri(frame_png(pal, frames[n], scale=8)) for n in order}
    (OUT / "Pancho Bot.html").write_text(SHOWCASE.format(**uris), encoding="utf-8")
    print("  Pancho Bot.html             self-contained animated showcase")

    (OUT / "README.txt").write_text(
        "PANCHO BOT\n"
        "==========\n\n"
        "Open 'Pancho Bot.html' first — it animates, and it is a single file with the\n"
        "art inlined, so it works with no internet and nothing installed.\n\n"
        "png/     transparent PNGs of each frame at 1x (the true 28x28 art), 4x, 8x, 16x,\n"
        "         plus spritesheets laid out idle | blink | wag.\n"
        "         Scale them by whole numbers only and turn off smoothing, or the pixels\n"
        "         go blurry (CSS: image-rendering: pixelated).\n\n"
        "pancho-sprite.json\n"
        "         The actual design: a 14-colour palette and three 28x28 grids of\n"
        "         characters. '.' is transparent, every other letter maps to a colour.\n"
        "         Edit a character, re-render, and the art changes.\n\n"
        "Frames:  idle  - resting\n"
        "         blink - eyes closed, 150ms\n"
        "         wag   - tail up; alternate with idle every ~140ms\n",
        encoding="utf-8")
    print("  README.txt\n")

    print(to_text(pal, frames["idle"]))
    print("\nwrote %s" % OUT)


if __name__ == "__main__":
    main()
