import pytest

from appstore_mockup.config import template_radius
from appstore_mockup.stores import asset_kind, check_canvas


@pytest.mark.parametrize(
    ("size", "kind"),
    [
        ((2007, 2853), "iPhone Duo inner display"),
        ((2853, 2007), "iPhone Duo inner display"),
        ((1398, 2034), "iPhone Duo outer display"),
        ((1320, 2868), "iPhone with Dynamic Island (large display)"),
        ((3840, 1646), "Product page header (21:9)"),
        ((3840, 2560), "Search results (3:2)"),
        ((1920, 1280), "Search results (3:2)"),
    ],
)
def test_asset_kind_recognises_apple_sizes(size, kind):
    assert asset_kind(*size) == kind
    assert check_canvas(*size) is None


@pytest.mark.parametrize("size", [(400, 800), (1646, 3840), (4200, 2800), (1500, 1000)])
def test_check_canvas_warns_on_other_sizes(size):
    assert "matches no App Store" in check_canvas(*size)


def test_duo_templates_match_simulator_corners():
    assert template_radius("duo", 2007) == 165
    assert template_radius("duo-outer", 1398) == 177
