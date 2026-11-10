"""Collect the Microsoft Store uploads into _build/msstore as flattened RGB PNGs."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parent.parent
out = root / "_build" / "msstore"
(out / "screenshots").mkdir(parents=True, exist_ok=True)
items = {f"screenshots/{p.name}": p for p in sorted((root / "_build/msstore-screenshots/previews").glob("*.png"))}
items |= {
    "super-hero-art-3840x2160.png": root / "_build/msstore-hero/previews/super-hero-art.png",
    "poster-art-1440x2160.png": root / "_build/msstore-poster/previews/poster-art.png",
    "box-art-2160x2160.png": root / "_build/msstore-boxart/previews/box-art.png",
    "app-tile-icon-300x300.png": root / "_brand/app-tile-300.png",
}
for name, src in items.items():
    img = Image.open(src)
    if img.mode != "RGB":
        bg = Image.new("RGB", img.size, "#006E39")
        bg.paste(img, mask=img.getchannel("A") if "A" in img.mode else None)
        img = bg
    img.save(out / name, optimize=True)
    print(f"{name:45} {img.size[0]}x{img.size[1]} {img.mode} {(out / name).stat().st_size / 1e6:.1f} MB")
