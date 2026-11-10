"""Brand inputs for the SEGUI Microsoft Store art.

Run from this folder after rendering mark.png with render.py:

    uv run python brand.py

Writes:
- mark-trim.png: the logo mark cropped to its ink, transparent.
- app-tile-300.png: the 1:1 Store app tile icon (300x300) from the launcher icon.
- matrix.png: an abstract alignment-matrix pattern for the 16:9 hero art,
  transparent, 3840x2160, with no text or UI.
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).parent
LAUNCHER_ICON = Path("F:/Programming/Flutter/segui/assets/launcher/icon.png")

# Nucleotide-like palette drawn from the logo's gradient stroke.
PALETTE = ["#FFD64F", "#C6CE64", "#9CC874", "#66C188", "#33BA9C", "#FFFFFF"]


def trim_mark() -> None:
    mark = Image.open(HERE / "mark.png").convert("RGBA")
    mark.crop(mark.getbbox()).save(HERE / "mark-trim.png")


def app_tile() -> None:
    icon = Image.open(LAUNCHER_ICON).convert("RGB")
    icon.resize((300, 300), Image.Resampling.LANCZOS).save(HERE / "app-tile-300.png")


def matrix(width: int = 3840, height: int = 2160, seed: int = 11) -> None:
    """Rows of rounded cells like an alignment, fading towards the centre."""
    rng = random.Random(seed)
    scale = 2
    canvas = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    cell_w, cell_h, gap = 64 * scale, 64 * scale, 14 * scale
    cols = width * scale // (cell_w + gap) + 2
    rows = height * scale // (cell_h + gap) + 2
    cx, cy = width * scale / 2, height * scale * 0.44
    for r in range(rows):
        # Each row is a "sequence": runs of the same base, with gaps.
        c = 0
        x_offset = -(r * 23 * scale % (cell_w + gap))
        while c < cols:
            run = rng.randint(1, 6)
            color = rng.choice(PALETTE)
            is_gap = rng.random() < 0.18
            for _ in range(run):
                if c >= cols:
                    break
                x = x_offset + c * (cell_w + gap)
                y = r * (cell_h + gap)
                # Fade cells near the mark so the centre stays clear.
                dx = (x + cell_w / 2 - cx) / (width * scale * 0.5)
                dy = (y + cell_h / 2 - cy) / (height * scale * 0.5)
                dist = (dx * dx * 1.0 + dy * dy * 1.6) ** 0.5
                alpha = max(0.0, min(1.0, (dist - 0.38) / 0.55))
                alpha *= rng.uniform(0.35, 0.8)
                if not is_gap and alpha > 0.02:
                    rgb = Image.new("RGB", (1, 1), color).getpixel((0, 0))
                    draw.rounded_rectangle(
                        (x, y, x + cell_w, y + cell_h),
                        radius=16 * scale,
                        fill=(*rgb, int(255 * alpha)),
                    )
                elif is_gap and alpha > 0.02:
                    draw.rounded_rectangle(
                        (x + 8 * scale, y + cell_h / 2 - 4 * scale, x + cell_w - 8 * scale, y + cell_h / 2 + 4 * scale),
                        radius=4 * scale,
                        fill=(255, 255, 255, int(160 * alpha)),
                    )
                c += 1
    canvas = canvas.resize((width, height), Image.Resampling.LANCZOS)
    canvas = canvas.filter(ImageFilter.GaussianBlur(0.6))
    canvas.save(HERE / "matrix.png")


if __name__ == "__main__":
    trim_mark()
    app_tile()
    matrix()
