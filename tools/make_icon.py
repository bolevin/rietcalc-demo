"""Draw the application icon: a coordination octahedron on an accent tile.

    python tools/make_icon.py

Writes ``icon.png`` (256 px) and a multi-size ``icon.ico`` into the package data.
The tile and its gradient match the RietESD Demo icon; the motif - a central atom
bonded to six neighbours, drawn in projection - is what this program measures.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "src" / "rietcalc_demo" / "data"
SIZE = 1024  # drawn large, downsampled for smooth edges
TOP, BOTTOM = (0, 120, 212), (0, 62, 146)  # accent gradient, shared with RietESD Demo
WHITE = (255, 255, 255, 255)
SOFT = (255, 255, 255, 150)


def main() -> None:
    tile = Image.new("RGBA", (SIZE, SIZE))
    for y in range(SIZE):
        t = y / (SIZE - 1)
        colour = tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM, strict=True))
        ImageDraw.Draw(tile).line([(0, y), (SIZE, y)], fill=(*colour, 255))
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=220, fill=255)
    icon = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    icon.paste(tile, (0, 0), mask)
    draw = ImageDraw.Draw(icon)

    centre = (512, 512)
    # four equatorial neighbours (a slightly tilted square seen from above) and two
    # apical ones; the back two are drawn softer to give the octahedron its depth
    front = [(232, 600), (792, 424), (512, 170), (512, 854)]
    back = [(300, 380), (724, 644)]
    for x, y in back:
        draw.line([centre, (x, y)], fill=SOFT, width=34)
    for x, y in back:
        draw.ellipse([x - 62, y - 62, x + 62, y + 62], fill=SOFT)
    for x, y in front:
        draw.line([centre, (x, y)], fill=WHITE, width=44)
    for x, y in front:
        draw.ellipse([x - 78, y - 78, x + 78, y + 78], fill=WHITE)
    cx, cy = centre
    draw.ellipse([cx - 112, cy - 112, cx + 112, cy + 112], fill=WHITE)
    draw.ellipse([cx - 64, cy - 64, cx + 64, cy + 64], fill=(0, 92, 180, 255))

    OUT.mkdir(parents=True, exist_ok=True)
    icon.resize((256, 256), Image.LANCZOS).save(OUT / "icon.png")
    icon.save(OUT / "icon.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    print(f"wrote {OUT / 'icon.png'} and icon.ico")


if __name__ == "__main__":
    main()
