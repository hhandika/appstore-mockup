"""App Store asset sizes accepted by App Store Connect.

From Apple's screenshot and creative asset specifications, October 2026. Sizes are
portrait or as listed; the landscape form of a screenshot size is accepted too.
"""

SCREENSHOT_SIZES: dict[str, list[tuple[int, int]]] = {
    "iPhone Duo inner display": [(2007, 2853)],
    "iPhone Duo outer display": [(1398, 2034)],
    "iPhone with Dynamic Island (large display)": [(1260, 2736), (1290, 2796), (1320, 2868)],
    "iPhone with Dynamic Island (medium display)": [(1179, 2556), (1206, 2622)],
    "iPad 13-inch": [(2064, 2752), (2048, 2732)],
}

# Creative assets are landscape only.
CREATIVE_SIZES: dict[str, list[tuple[int, int]]] = {
    "Product page header (21:9)": [(3840, 1646)],
    "Product page header or search results (16:9)": [(5244, 2950)],
}

# Search results images are 3:2, from 1920x1280 up to 3840x2560.
SEARCH_RESULTS_RANGE = ((1920, 1280), (3840, 2560))


def asset_kind(width: int, height: int) -> str | None:
    """The App Store asset a canvas of this size can be uploaded as, if any."""
    for name, sizes in SCREENSHOT_SIZES.items():
        if (width, height) in sizes or (height, width) in sizes:
            return name
    for name, sizes in CREATIVE_SIZES.items():
        if (width, height) in sizes:
            return name
    (low_w, low_h), (high_w, high_h) = SEARCH_RESULTS_RANGE
    if width * 2 == height * 3 and low_w <= width <= high_w and low_h <= height <= high_h:
        return "Search results (3:2)"
    return None


def check_canvas(width: int, height: int) -> str | None:
    """A warning when App Store Connect accepts no asset of this size, else None."""
    if asset_kind(width, height) is not None:
        return None
    return f"Canvas {width}x{height} matches no App Store screenshot or creative asset size"
