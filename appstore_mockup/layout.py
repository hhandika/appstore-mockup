"""Layout specs that describe store screenshots as stacked elements.

Positions and boxes are fractions of the canvas, so a layout reads the same at
any store size. Font sizes are pixels. Frame measurements are CSS pixels of a
reference panel, scaled by the canvas short side, so a frame tuned on a web
showcase keeps its proportions on a store canvas.
"""

from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, model_validator

from appstore_mockup.config import Template


class Canvas(BaseModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class GradientStop(BaseModel):
    color: str
    position: float = Field(ge=0, le=1)


class Gradient(BaseModel):
    """A linear gradient, named after the CSS direction keywords."""

    direction: Literal["to-bottom", "to-right", "to-bottom-right"] = "to-bottom-right"
    stops: list[GradientStop] = Field(min_length=1)


class FrameStyle(BaseModel):
    """A frosted glass mat around a screen, with a soft drop shadow."""

    reference: float = Field(default=500, gt=0)
    border: float = Field(default=5, ge=0)
    color: str = "#FFFFFF47"
    backdrop_blur: float = Field(default=10, ge=0)
    hairline: float = Field(default=1, ge=0)
    hairline_color: str = "#3993752E"
    shadow_offset_y: float = 18
    shadow_blur: float = Field(default=40, ge=0)
    shadow_spread: float = -20
    shadow_color: str = "#00000059"
    screen_color: str = "#0E251F"


class FontSpec(BaseModel):
    postscript_name: str
    # Used for the preview and for measuring lines; Pillow's default when unset.
    file: Path | None = None


class TextElement(BaseModel):
    type: Literal["text"] = "text"
    name: str | None = None
    text: str = Field(min_length=1)
    font: str
    size: float = Field(gt=0)
    color: str = "#0E251F"
    cx: float = 0.5
    # Top of the inked text block.
    top: float
    max_width: float = Field(default=0.9, gt=0)
    line_height: float = Field(default=1.2, gt=0)
    # Thousandths of an em, as in Photoshop.
    tracking: int = 0


class Retouch(BaseModel):
    """Paints out a stroke of one colour, such as a screenshot gesture mark.

    Pixels in box that are within tolerance of color, grown by grow pixels to
    catch anti-aliasing, are filled in from their surroundings.
    """

    # Left, top, right, and bottom edges in source pixels, before cropping.
    box: tuple[int, int, int, int]
    color: str
    tolerance: int = Field(default=48, ge=0, le=255)
    grow: int = Field(default=2, ge=0)


class DeviceElement(BaseModel):
    """An app screen inside a glass frame."""

    type: Literal["device"] = "device"
    name: str | None = None
    image: Path
    # Folder for this image instead of the spec's source_dir.
    source_dir: Path | None = None
    template: Template = "ios"
    # Corner radius in source pixels; the template default when unset.
    radius: int | None = Field(default=None, ge=0)
    # Pixels trimmed from the left, top, right, and bottom of the source.
    crop: tuple[int, int, int, int] = (0, 0, 0, 0)
    retouch: list[Retouch] = Field(default_factory=list)
    cx: float = 0.5
    cy: float = 0.5
    max_width: float = Field(default=1.0, gt=0)
    max_height: float = Field(default=1.0, gt=0)


class ImageElement(BaseModel):
    """A plain image, such as a logo, placed without a frame."""

    type: Literal["image"] = "image"
    name: str | None = None
    image: Path
    # Folder for this image instead of the spec's source_dir.
    source_dir: Path | None = None
    cx: float = 0.5
    cy: float = 0.5
    max_width: float = Field(default=1.0, gt=0)
    max_height: float = Field(default=1.0, gt=0)
    opacity: float = Field(default=1.0, ge=0, le=1)


Element = Annotated[
    Union[TextElement, DeviceElement, ImageElement], Field(discriminator="type")
]


class Screen(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9._-]+$")
    elements: list[Element]


class LayoutSpec(BaseModel):
    canvas: Canvas
    background: Gradient
    frame: FrameStyle = Field(default_factory=FrameStyle)
    fonts: dict[str, FontSpec] = Field(default_factory=dict)
    source_dir: Path = Path(".")
    screens: list[Screen] = Field(min_length=1)

    @model_validator(mode="after")
    def check_references(self) -> "LayoutSpec":
        seen: set[str] = set()
        for screen in self.screens:
            if screen.id in seen:
                raise ValueError(f"Duplicate screen id '{screen.id}'")
            seen.add(screen.id)
            for element in screen.elements:
                if isinstance(element, TextElement) and element.font not in self.fonts:
                    raise ValueError(
                        f"Screen '{screen.id}' uses undefined font '{element.font}'"
                    )
        return self

    @classmethod
    def load(cls, path: str | Path) -> "LayoutSpec":
        """Reads a spec, resolving relative paths against its directory."""
        path = Path(path)
        spec = cls.model_validate_json(path.read_text(encoding="utf-8"))
        return spec.relative_to(path.parent)

    def relative_to(self, base: Path) -> "LayoutSpec":
        fonts = {
            key: font.model_copy(update={"file": _anchor(font.file, base)})
            if font.file is not None
            else font
            for key, font in self.fonts.items()
        }
        screens = [
            screen.model_copy(
                update={"elements": [_anchor_element(element, base) for element in screen.elements]}
            )
            for screen in self.screens
        ]
        return self.model_copy(
            update={
                "source_dir": _anchor(self.source_dir, base),
                "fonts": fonts,
                "screens": screens,
            }
        )

    def image_path(self, element: "DeviceElement | ImageElement") -> Path:
        return (element.source_dir or self.source_dir) / element.image


def _anchor(path: Path, base: Path) -> Path:
    path = path.expanduser()
    return path if path.is_absolute() else base / path


def _anchor_element(element: Element, base: Path) -> Element:
    if isinstance(element, TextElement) or element.source_dir is None:
        return element
    return element.model_copy(update={"source_dir": _anchor(element.source_dir, base)})
