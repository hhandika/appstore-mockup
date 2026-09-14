from pydantic import BaseModel, Field
from typing import Optional, Literal

Template = Literal["ios", "ipad", "macos", "android", "pc"]

# Display corner radius in points, and the logical screen width it belongs to.
TEMPLATE_RADII: dict[str, tuple[float, int]] = {
    "ios": (47.33, 393),       # iPhone 15 Pro
    "ipad": (18, 834),         # iPad Pro 11"
    "android": (36, 412),      # Pixel 8
    "macos": (16, 1440),       # MacBook Pro
    "pc": (8, 1504),           # Surface Laptop
}

def template_radius(template: str, image_width: int) -> int:
    """Corner radius in pixels for a screenshot of the given width."""
    pts, logical_width = TEMPLATE_RADII.get(template, TEMPLATE_RADII["ios"])
    return int(image_width * (pts / logical_width))

class MockupConfig(BaseModel):
    format: Literal["png", "webp"] = "png"
    border_type: Literal["color", "blur"] = "color"
    border_size: int = Field(default=0, ge=0)
    border_color: str = "#FFFFFF"
    radius: Optional[int] = Field(default=None, ge=0)
    template: Template = "ios"
