"""Compose store screenshots from app screens, glass frames, and captions.

Each screen is rendered as a flattened preview and as the separate layers a
Photoshop master is assembled from. A JSON manifest records how the layers
stack, so the master and the preview come from the same geometry.
"""

import io
import json
import math
from pathlib import Path

from PIL import (
    Image,
    ImageChops,
    ImageCms,
    ImageColor,
    ImageDraw,
    ImageFilter,
    ImageFont,
)

from appstore_mockup.config import template_radius
from appstore_mockup.layout import (
    DeviceElement,
    Element,
    ImageElement,
    LayoutSpec,
    Retouch,
    Screen,
    TextElement,
)

MANIFEST_VERSION = 1
# Masks are drawn this many times larger, then reduced, to smooth their edges.
SUPERSAMPLE = 4

Box = tuple[float, float, float, float]
Region = tuple[int, int, int, int]

_SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
_SRGB_BYTES = _SRGB.tobytes()


def parse_color(color: str) -> tuple[int, int, int, int]:
    value = ImageColor.getrgb(color)
    return value if len(value) == 4 else (*value, 255)


def load_srgb(path: Path, mode: str = "RGB") -> Image.Image:
    """Opens an image and converts it to sRGB, honouring an embedded profile."""
    with Image.open(path) as image:
        image.load()
        icc = image.info.get("icc_profile")
        converted = image.convert(mode)
    if not icc:
        return converted
    try:
        source = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        return ImageCms.profileToProfile(converted, source, _SRGB, outputMode=mode)
    except ImageCms.PyCMSError:
        return converted


class ScreenComposer:
    """Renders the screens of a layout spec."""

    def __init__(self, spec: LayoutSpec):
        self.spec = spec
        self.size = (spec.canvas.width, spec.canvas.height)
        self.scale = min(self.size) / spec.frame.reference

    def compose_all(self, output_dir: str | Path, only: list[str] | None = None) -> Path:
        """Composes every screen, or those in only, and returns the manifest path."""
        output_dir = Path(output_dir)
        screens = [screen for screen in self.spec.screens if not only or screen.id in only]
        entries = [self.compose(screen, output_dir) for screen in screens]
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / "manifest.json"
        manifest = {"version": MANIFEST_VERSION, "screens": entries}
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest_path

    def compose(self, screen: Screen, output_dir: str | Path) -> dict:
        output_dir = Path(output_dir)
        layer_dir = output_dir / "layers" / screen.id
        layer_dir.mkdir(parents=True, exist_ok=True)

        canvas = self.render_background()
        layers = [self._save_layer(layer_dir / "00-background.png", "Background", canvas)]
        for index, element in enumerate(screen.elements, start=1):
            canvas, entry = self._add_element(canvas, element, layer_dir, index)
            layers.append(entry)

        preview_dir = output_dir / "previews"
        preview_dir.mkdir(parents=True, exist_ok=True)
        preview_path = preview_dir / f"{screen.id}.png"
        canvas.convert("RGB").save(preview_path, icc_profile=_SRGB_BYTES)
        return {
            "id": screen.id,
            "canvas": list(self.size),
            "preview": str(preview_path.resolve()),
            "layers": layers,
        }

    def render_background(self) -> Image.Image:
        width, height = self.size
        direction = self.spec.background.direction
        vertical = Image.linear_gradient("L").resize((width, height), Image.Resampling.BILINEAR)
        horizontal = (
            Image.linear_gradient("L")
            .transpose(Image.Transpose.ROTATE_90)
            .resize((width, height), Image.Resampling.BILINEAR)
        )
        if direction == "to-bottom":
            index = vertical
        elif direction == "to-right":
            index = horizontal
        else:
            # CSS "to bottom right": the top-right and bottom-left corners meet
            # the gradient midpoint, so position is x / 2w + y / 2h.
            index = ImageChops.add(
                vertical.point(lambda value: value // 2),
                horizontal.point(lambda value: value // 2),
            )
        colors = [self._gradient_color(level / 255) for level in range(256)]
        bands = [index.point([color[band] for color in colors]) for band in range(3)]
        return Image.merge("RGB", bands).convert("RGBA")

    def device_box(self, element: DeviceElement | ImageElement, source_size: tuple[int, int]) -> Region:
        """Where a source of the given size lands on the canvas: x, y, width, height."""
        max_width = element.max_width * self.size[0]
        max_height = element.max_height * self.size[1]
        ratio = min(max_width / source_size[0], max_height / source_size[1])
        width = max(1, round(source_size[0] * ratio))
        height = max(1, round(source_size[1] * ratio))
        x = round(element.cx * self.size[0] - width / 2)
        y = round(element.cy * self.size[1] - height / 2)
        return x, y, width, height

    def wrap_lines(self, element: TextElement, font: ImageFont.FreeTypeFont) -> list[str]:
        """Breaks text on explicit newlines, then wherever a line outgrows max_width."""
        limit = element.max_width * self.size[0]
        extra = element.tracking / 1000 * element.size
        lines: list[str] = []
        for paragraph in element.text.split("\n"):
            current = ""
            for word in paragraph.split():
                candidate = f"{current} {word}".strip()
                if current and _line_width(candidate, font, extra) > limit:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            lines.append(current)
        return lines

    def _add_element(
        self, canvas: Image.Image, element: Element, layer_dir: Path, index: int
    ) -> tuple[Image.Image, dict]:
        if isinstance(element, DeviceElement):
            return self._add_device(canvas, element, layer_dir, index)
        if isinstance(element, ImageElement):
            return self._add_image(canvas, element, layer_dir, index)
        return self._add_text(canvas, element, index)

    def _add_device(
        self, canvas: Image.Image, element: DeviceElement, layer_dir: Path, index: int
    ) -> tuple[Image.Image, dict]:
        frame = self.spec.frame
        source = load_srgb(self.spec.image_path(element))
        for retouch in element.retouch:
            source = retouch_stroke(source, retouch)
        left, top, right, bottom = element.crop
        source = source.crop((left, top, source.width - right, source.height - bottom))

        x, y, width, height = self.device_box(element, source.size)
        source_radius = (
            element.radius
            if element.radius is not None
            else template_radius(element.template, source.width)
        )
        radius = source_radius * width / source.width
        border = frame.border * self.scale
        screen_box = (x, y, x + width, y + height)
        outer_box = (x - border, y - border, x + width + border, y + height + border)
        outer_radius = radius + border

        # The mat blurs what is behind the device, which excludes its own shadow.
        mat = self._glass_mat(canvas, outer_box, outer_radius, screen_box, radius)
        shadow = self._shadow(outer_box, outer_radius)
        canvas = Image.alpha_composite(canvas, shadow)
        canvas = Image.alpha_composite(canvas, mat)

        screen_mask = self._mask(screen_box, radius)
        shape = Image.new("RGBA", self.size, parse_color(frame.screen_color))
        shape.putalpha(screen_mask)
        content = Image.new("RGBA", self.size, (0, 0, 0, 0))
        content.paste(source.resize((width, height), Image.Resampling.LANCZOS), (x, y))
        content.putalpha(screen_mask)
        canvas = Image.alpha_composite(canvas, content)

        prefix = f"{index:02d}"
        source_path = layer_dir / f"{prefix}-screenshot.png"
        source.save(source_path, icc_profile=_SRGB_BYTES)
        entry = {
            "kind": "group",
            "name": element.name or f"Device {index}",
            "layers": [
                self._save_layer(layer_dir / f"{prefix}-shadow.png", "Shadow", shadow),
                self._save_layer(layer_dir / f"{prefix}-glass-mat.png", "Glass mat", mat),
                self._save_layer(layer_dir / f"{prefix}-screen-shape.png", "Screen shape", shape),
                {
                    "kind": "smart",
                    "name": "Screenshot",
                    "file": str(source_path.resolve()),
                    "box": [x, y, width, height],
                    "clip": True,
                },
            ],
        }
        return canvas, entry

    def _add_image(
        self, canvas: Image.Image, element: ImageElement, layer_dir: Path, index: int
    ) -> tuple[Image.Image, dict]:
        source = load_srgb(self.spec.image_path(element), mode="RGBA")
        x, y, width, height = self.device_box(element, source.size)
        layer = Image.new("RGBA", self.size, (0, 0, 0, 0))
        layer.paste(source.resize((width, height), Image.Resampling.LANCZOS), (x, y))
        if element.opacity < 1:
            alpha = layer.getchannel("A").point(lambda value: round(value * element.opacity))
            layer.putalpha(alpha)
        canvas = Image.alpha_composite(canvas, layer)
        name = element.name or Path(element.image).stem
        entry = self._save_layer(layer_dir / f"{index:02d}-image.png", name, layer)
        return canvas, entry

    def _add_text(
        self, canvas: Image.Image, element: TextElement, index: int
    ) -> tuple[Image.Image, dict]:
        font_spec = self.spec.fonts[element.font]
        if font_spec.file is not None:
            font = ImageFont.truetype(str(font_spec.file), element.size)
        else:
            font = ImageFont.load_default(element.size)
        lines = self.wrap_lines(element, font)
        leading = element.size * element.line_height
        extra = element.tracking / 1000 * element.size
        cx = element.cx * self.size[0]

        # Measure at the origin, then move the inked block to its place.
        ink = _draw_lines(None, lines, font, (cx, 0), leading, extra, element.color)
        offset = (cx - (ink[0] + ink[2]) / 2, element.top * self.size[1] - ink[1])
        layer = Image.new("RGBA", self.size, (0, 0, 0, 0))
        ink = _draw_lines(
            ImageDraw.Draw(layer),
            lines,
            font,
            (cx + offset[0], offset[1]),
            leading,
            extra,
            element.color,
        )
        canvas = Image.alpha_composite(canvas, layer)
        red, green, blue, _ = parse_color(element.color)
        entry = {
            "kind": "text",
            "name": element.name or f"Text {index}",
            "lines": lines,
            "font": font_spec.postscript_name,
            "size": element.size,
            "color": f"#{red:02X}{green:02X}{blue:02X}",
            "tracking": element.tracking,
            "leading": leading,
            "cx": (ink[0] + ink[2]) / 2,
            "ink_top": ink[1],
            "ink_box": list(ink),
        }
        return canvas, entry

    def _glass_mat(
        self,
        canvas: Image.Image,
        outer_box: Box,
        outer_radius: float,
        inner_box: Box,
        inner_radius: float,
    ) -> Image.Image:
        frame = self.spec.frame
        ring = ImageChops.subtract(
            self._mask(outer_box, outer_radius), self._mask(inner_box, inner_radius)
        )
        sigma = frame.backdrop_blur * self.scale
        region = self._region(outer_box, math.ceil(sigma * 3))
        backdrop = canvas.crop(region)
        if sigma > 0:
            backdrop = backdrop.filter(ImageFilter.GaussianBlur(sigma))
        tint = Image.new("RGBA", backdrop.size, parse_color(frame.color))
        mat = Image.new("RGBA", self.size, (0, 0, 0, 0))
        mat.paste(Image.alpha_composite(backdrop, tint), region[:2])
        mat.putalpha(ring)

        hairline = frame.hairline * self.scale
        if hairline <= 0:
            return mat
        edge_box = (
            outer_box[0] - hairline,
            outer_box[1] - hairline,
            outer_box[2] + hairline,
            outer_box[3] + hairline,
        )
        edge = ImageChops.subtract(
            self._mask(edge_box, outer_radius + hairline), self._mask(outer_box, outer_radius)
        )
        return Image.alpha_composite(mat, _tinted(self.size, frame.hairline_color, edge))

    def _shadow(self, outer_box: Box, outer_radius: float) -> Image.Image:
        frame = self.spec.frame
        spread = frame.shadow_spread * self.scale
        offset = frame.shadow_offset_y * self.scale
        # A CSS blur radius is twice the standard deviation.
        sigma = frame.shadow_blur * self.scale / 2
        box = (
            outer_box[0] - spread,
            outer_box[1] - spread + offset,
            outer_box[2] + spread,
            outer_box[3] + spread + offset,
        )
        mask = self._mask(box, max(0.0, outer_radius + spread))
        if sigma > 0:
            region = self._region(box, math.ceil(sigma * 3))
            blurred = mask.crop(region).filter(ImageFilter.GaussianBlur(sigma))
            mask = Image.new("L", self.size, 0)
            mask.paste(blurred, region[:2])
        return _tinted(self.size, frame.shadow_color, mask)

    def _mask(self, box: Box, radius: float) -> Image.Image:
        """An anti-aliased rounded rectangle on a canvas-sized mask."""
        left, top = math.floor(box[0]) - 1, math.floor(box[1]) - 1
        right, bottom = math.ceil(box[2]) + 1, math.ceil(box[3]) + 1
        region_size = (right - left, bottom - top)
        radius = max(0.0, min(radius, (box[2] - box[0]) / 2, (box[3] - box[1]) / 2))
        large = Image.new("L", (region_size[0] * SUPERSAMPLE, region_size[1] * SUPERSAMPLE), 0)
        ImageDraw.Draw(large).rounded_rectangle(
            (
                (box[0] - left) * SUPERSAMPLE,
                (box[1] - top) * SUPERSAMPLE,
                (box[2] - left) * SUPERSAMPLE - 1,
                (box[3] - top) * SUPERSAMPLE - 1,
            ),
            radius=radius * SUPERSAMPLE,
            fill=255,
        )
        mask = Image.new("L", self.size, 0)
        mask.paste(large.resize(region_size, Image.Resampling.BOX), (left, top))
        return mask

    def _region(self, box: Box, pad: int) -> Region:
        """Box grown by pad and clamped to the canvas, as integer pixel edges."""
        return (
            max(0, math.floor(box[0]) - pad),
            max(0, math.floor(box[1]) - pad),
            min(self.size[0], math.ceil(box[2]) + pad),
            min(self.size[1], math.ceil(box[3]) + pad),
        )

    def _gradient_color(self, position: float) -> tuple[int, int, int]:
        stops = sorted(self.spec.background.stops, key=lambda stop: stop.position)
        colors = [parse_color(stop.color)[:3] for stop in stops]
        if position <= stops[0].position:
            return colors[0]
        for (start, end), (low, high) in zip(
            zip(stops, stops[1:]), zip(colors, colors[1:])
        ):
            if position <= end.position:
                span = end.position - start.position
                fraction = 0 if span == 0 else (position - start.position) / span
                return tuple(round(a + (b - a) * fraction) for a, b in zip(low, high))
        return colors[-1]

    def _save_layer(self, path: Path, name: str, image: Image.Image) -> dict:
        image.save(path, icc_profile=_SRGB_BYTES)
        return {"kind": "raster", "name": name, "file": str(path.resolve())}


def retouch_stroke(image: Image.Image, retouch: Retouch) -> Image.Image:
    """Fills a stroke of one colour with the average of its surroundings, ring by ring."""
    box = (
        max(0, retouch.box[0]),
        max(0, retouch.box[1]),
        min(image.width, retouch.box[2]),
        min(image.height, retouch.box[3]),
    )
    if box[2] <= box[0] or box[3] <= box[1]:
        return image
    region = image.crop(box)
    pixels = region.load()
    width, height = region.size
    target = parse_color(retouch.color)[:3]

    stroke = {
        (x, y)
        for x in range(width)
        for y in range(height)
        if max(abs(a - b) for a, b in zip(pixels[x, y][:3], target)) <= retouch.tolerance
    }
    for _ in range(retouch.grow):
        stroke |= {
            (x + dx, y + dy)
            for x, y in stroke
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if 0 <= x + dx < width and 0 <= y + dy < height
        }

    neighbours = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
    minimum = 3
    while stroke:
        filled = {}
        for x, y in stroke:
            known = [
                pixels[x + dx, y + dy]
                for dx, dy in neighbours
                if 0 <= x + dx < width
                and 0 <= y + dy < height
                and (x + dx, y + dy) not in stroke
            ]
            if len(known) >= minimum:
                filled[(x, y)] = tuple(
                    round(sum(color[band] for color in known) / len(known))
                    for band in range(len(known[0]))
                )
        if not filled:
            if minimum == 1:
                break
            minimum -= 1
            continue
        for point, color in filled.items():
            pixels[point] = color
        stroke -= filled.keys()

    retouched = image.copy()
    retouched.paste(region, box[:2])
    return retouched


def _tinted(size: tuple[int, int], color: str, mask: Image.Image) -> Image.Image:
    """A solid colour layer whose opacity follows mask, scaled by the colour alpha."""
    red, green, blue, alpha = parse_color(color)
    layer = Image.new("RGBA", size, (red, green, blue, 0))
    layer.putalpha(mask.point(lambda value: value * alpha // 255))
    return layer


def _line_width(line: str, font: ImageFont.FreeTypeFont, extra: float) -> float:
    if extra == 0:
        return font.getlength(line)
    return sum(font.getlength(char) for char in line) + extra * max(0, len(line) - 1)


def _draw_lines(
    draw: ImageDraw.ImageDraw | None,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    origin: tuple[float, float],
    leading: float,
    extra: float,
    fill: str,
) -> Box:
    """Draws centred lines from the first baseline at origin and returns the ink box."""
    measure = draw or ImageDraw.Draw(Image.new("L", (1, 1)))
    boxes = []
    for number, line in enumerate(lines):
        baseline = origin[1] + number * leading
        if extra == 0:
            position = (origin[0], baseline)
            boxes.append(measure.textbbox(position, line, font=font, anchor="ms"))
            if draw:
                draw.text(position, line, font=font, fill=fill, anchor="ms")
            continue
        x = origin[0] - _line_width(line, font, extra) / 2
        for char in line:
            boxes.append(measure.textbbox((x, baseline), char, font=font, anchor="ls"))
            if draw:
                draw.text((x, baseline), char, font=font, fill=fill, anchor="ls")
            x += font.getlength(char) + extra
    inked = [box for box in boxes if box[2] > box[0]] or boxes
    return (
        min(box[0] for box in inked),
        min(box[1] for box in inked),
        max(box[2] for box in inked),
        max(box[3] for box in inked),
    )
