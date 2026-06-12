import pytest
from PIL import Image
from appstore_mockup.editor import apply_rounded_corners, apply_color_border, apply_glass_border

@pytest.fixture
def sample_image():
    return Image.new("RGBA", (100, 100), (255, 0, 0, 255))

def test_apply_rounded_corners(sample_image):
    result = apply_rounded_corners(sample_image, 10)
    assert result.size == (100, 100)
    # The corner should be fully transparent
    assert result.getpixel((0, 0))[3] == 0
    # The center should still be opaque
    assert result.getpixel((50, 50))[3] == 255

def test_apply_color_border(sample_image):
    border_size = 10
    radius = 5
    result = apply_color_border(sample_image, border_size, "#00FF00", radius)
    
    assert result.size == (120, 120)

def test_apply_glass_border(sample_image):
    border_size = 15
    radius = 10
    result = apply_glass_border(sample_image, border_size, radius)
    
    assert result.size == (130, 130)

def test_no_effect_when_zero(sample_image):
    res1 = apply_rounded_corners(sample_image, 0)
    assert res1 == sample_image
    
    res2 = apply_color_border(sample_image, 0, "#FFF", 0)
    assert res2 == sample_image
    
    res3 = apply_glass_border(sample_image, 0, 0)
    assert res3 == sample_image
