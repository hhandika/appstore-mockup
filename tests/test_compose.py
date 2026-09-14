import json

import pytest
from PIL import Image
from pydantic import ValidationError

from appstore_mockup.cli import parse_args, parse_compose_args, parse_photoshop_args
from appstore_mockup.compose import ScreenComposer, retouch_stroke
from appstore_mockup.layout import LayoutSpec, Retouch
from appstore_mockup.photoshop import PhotoshopBuilder


def make_spec(tmp_path, **overrides) -> dict:
    Image.new("RGB", (60, 120), "blue").save(tmp_path / "phone.png")
    Image.new("RGBA", (40, 40), (255, 0, 0, 128)).save(tmp_path / "logo.png")
    spec = {
        "canvas": {"width": 400, "height": 800},
        "background": {
            "direction": "to-bottom-right",
            "stops": [
                {"color": "#000000", "position": 0},
                {"color": "#FFFFFF", "position": 1},
            ],
        },
        "fonts": {"headline": {"postscript_name": "Merriweather-Bold"}},
        "source_dir": ".",
        "screens": [
            {
                "id": "01-home",
                "elements": [
                    {
                        "type": "text",
                        "text": "One catalog per expedition",
                        "font": "headline",
                        "size": 28,
                        "top": 0.05,
                        "max_width": 0.5,
                    },
                    {
                        "type": "device",
                        "name": "Phone",
                        "image": "phone.png",
                        "cx": 0.5,
                        "cy": 0.6,
                        "max_width": 0.8,
                        "max_height": 0.5,
                    },
                    {"type": "image", "image": "logo.png", "cx": 0.9, "cy": 0.9, "max_width": 0.1},
                ],
            }
        ],
    }
    spec.update(overrides)
    return spec


@pytest.fixture
def composed(tmp_path):
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(make_spec(tmp_path)))
    composer = ScreenComposer(LayoutSpec.load(spec_path))
    manifest_path = composer.compose_all(tmp_path / "out")
    return composer, json.loads(manifest_path.read_text())


def test_manifest_lists_layers_bottom_to_top(composed):
    _, manifest = composed
    screen = manifest["screens"][0]
    assert screen["canvas"] == [400, 800]
    assert [layer["kind"] for layer in screen["layers"]] == ["raster", "text", "group", "raster"]

    group = screen["layers"][2]
    assert group["name"] == "Phone"
    assert [layer["name"] for layer in group["layers"]] == [
        "Shadow",
        "Glass mat",
        "Screen shape",
        "Screenshot",
    ]
    assert group["layers"][3]["clip"] is True


def test_layers_and_preview_match_canvas(composed):
    _, manifest = composed
    screen = manifest["screens"][0]
    with Image.open(screen["preview"]) as preview:
        assert preview.size == (400, 800)
        assert preview.mode == "RGB"
    with Image.open(screen["layers"][2]["layers"][1]["file"]) as mat:
        assert mat.size == (400, 800)
        assert mat.mode == "RGBA"


def test_device_fits_its_box_and_centre(composed):
    _, manifest = composed
    x, y, width, height = manifest["screens"][0]["layers"][2]["layers"][3]["box"]
    assert height == 400
    assert width == 200
    assert x + width / 2 == pytest.approx(200, abs=1)
    assert y + height / 2 == pytest.approx(480, abs=1)


def test_screenshot_source_keeps_full_resolution(composed):
    _, manifest = composed
    source = manifest["screens"][0]["layers"][2]["layers"][3]["file"]
    with Image.open(source) as image:
        assert image.size == (60, 120)


def test_glass_mat_is_a_ring(composed):
    _, manifest = composed
    x, y, width, height = manifest["screens"][0]["layers"][2]["layers"][3]["box"]
    with Image.open(manifest["screens"][0]["layers"][2]["layers"][1]["file"]) as mat:
        alpha = mat.getchannel("A")
        assert alpha.getpixel((x + width // 2, y + height // 2)) == 0
        assert alpha.getpixel((x + width // 2, y - 3)) > 0


def test_text_wraps_and_sits_at_top(composed):
    _, manifest = composed
    text = manifest["screens"][0]["layers"][1]
    assert len(text["lines"]) > 1
    assert text["ink_top"] == pytest.approx(40, abs=1)
    assert text["cx"] == pytest.approx(200, abs=1)
    assert text["font"] == "Merriweather-Bold"


def test_background_follows_gradient(composed):
    composer, _ = composed
    background = composer.render_background()
    assert background.getpixel((0, 0))[0] < 10
    assert background.getpixel((399, 799))[0] > 245
    assert background.getpixel((399, 0))[0] == pytest.approx(127, abs=3)


def test_only_limits_screens(tmp_path):
    spec = make_spec(tmp_path)
    second = json.loads(json.dumps(spec["screens"][0]))
    second["id"] = "02-sites"
    spec["screens"].append(second)
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    manifest_path = ScreenComposer(LayoutSpec.load(spec_path)).compose_all(
        tmp_path / "out", only=["02-sites"]
    )
    manifest = json.loads(manifest_path.read_text())
    assert [screen["id"] for screen in manifest["screens"]] == ["02-sites"]


def test_retouch_paints_out_a_stroke():
    image = Image.new("RGB", (40, 40), (20, 30, 25))
    for offset in range(30):
        image.putpixel((5 + offset, 34 - offset), (255, 255, 255))
        image.putpixel((6 + offset, 34 - offset), (255, 255, 255))
    retouch = Retouch(box=(0, 0, 40, 40), color="#FFFFFF", tolerance=40)
    result = retouch_stroke(image, retouch)
    assert result.getpixel((20, 19)) == (20, 30, 25)
    assert result.getpixel((0, 0)) == (20, 30, 25)
    assert image.getpixel((20, 19)) == (255, 255, 255)


def test_spec_rejects_undefined_font(tmp_path):
    spec = make_spec(tmp_path, fonts={})
    with pytest.raises(ValidationError):
        LayoutSpec.model_validate(spec)


def test_spec_rejects_duplicate_ids(tmp_path):
    spec = make_spec(tmp_path)
    spec["screens"].append(spec["screens"][0])
    with pytest.raises(ValidationError):
        LayoutSpec.model_validate(spec)


def test_spec_resolves_paths_against_its_directory(tmp_path):
    spec = make_spec(tmp_path, source_dir="screens")
    spec["fonts"]["headline"]["file"] = "fonts/headline.ttf"
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    loaded = LayoutSpec.load(spec_path)
    assert loaded.source_dir == tmp_path / "screens"
    assert loaded.fonts["headline"].file == tmp_path / "fonts" / "headline.ttf"


def test_element_source_dir_overrides_spec_source_dir(tmp_path):
    spec = make_spec(tmp_path, source_dir="screens")
    spec["screens"][0]["elements"][1]["source_dir"] = "captures"
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    loaded = LayoutSpec.load(spec_path)
    device, image = loaded.screens[0].elements[1], loaded.screens[0].elements[2]
    assert loaded.image_path(device) == tmp_path / "captures" / "phone.png"
    assert loaded.image_path(image) == tmp_path / "screens" / "logo.png"


def test_subcommand_parsers_leave_legacy_usage_intact():
    assert parse_args(["shot.png", "--template", "ipad"]).template == "ipad"
    compose = parse_compose_args(["spec.json", "--only", "01", "02"])
    assert compose.only == ["01", "02"]
    photoshop = parse_photoshop_args(["manifest.json", "--psd-dir", "psd", "--png-dir", "png"])
    assert photoshop.psd_dir == "psd"


def test_applescript_escapes_quotes(tmp_path):
    builder = PhotoshopBuilder(app='Adobe "Photoshop"')
    script = builder.applescript(tmp_path / 'job "1".json')
    assert 'Adobe \\"Photoshop\\"' in script
    assert 'job \\"1\\".json' in script
