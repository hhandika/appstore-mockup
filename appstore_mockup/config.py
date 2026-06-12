from pydantic import BaseModel, Field
from typing import Optional, Literal

class MockupConfig(BaseModel):
    format: Literal["png", "webp"] = "png"
    border_type: Literal["color", "blur"] = "color"
    border_size: int = Field(default=0, ge=0)
    border_color: str = "#FFFFFF"
    radius: Optional[int] = Field(default=None, ge=0)
    template: Literal["ios", "macos", "android", "pc"] = "ios"
