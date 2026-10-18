# appstore-mockup

A Python CLI utility to automate the creation of app store mockups. It allows you to style your raw app screenshots with rounded corners, solid color borders, or glassmorphism effects, preparing them for final store listings.

## Features

- **Rounded Corners**: Emulate native device display rounding (e.g., standard iOS corners).
- **Glass Borders**: Add a sleek, glass-like frosted border around your screenshots.
- **Color Borders**: Add crisp, solid color borders.
- **Batch Processing**: Process a single image or an entire directory of screenshots.
- **Transparent Exports**: Export directly to PNG or lossless WEBP with a transparent canvas.

## Installation

You can install the tool via `pip` or `uv`:

### Using pip

```bash
pip install appstore-mockup
```

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is an extremely fast Python package installer. Install the tool globally:

```bash
uv tool install appstore-mockup
```

Alternatively, you can run it directly without prior installation using `uvx`:

```bash
uvx appstore-mockup --help
```

## Usage

```bash
uvx appstore-mockup <input_path> [options]
```

### Options

| Option | Description | Default |
| :--- | :--- | :--- |
| `input` | **(Required)** Path to a single image file or a directory. | |
| `-o`, `--output-dir` | Target directory for the exported mockups. | `./output` |
| `-f`, `--format` | Export image format (`png` or `webp`). | `png` |
| `-t`, `--border-type` | Type of outer border (`color` or `blur`). | `color` |
| `--template` | Device template for default corner radius (`ios`, `duo`, `duo-outer`, `ipad`, `macos`, `android`, `pc`). | `ios` |
| `-s`, `--border-size` | Width of the outer border in pixels. | `0` |
| `-c`, `--border-color` | Hex or RGB color code for `color` border type. | `#FFFFFF` |
| `-r`, `--radius` | Corner rounding radius in pixels (overrides template). | template default |

### Templates

The `--template` option sets the default corner rounding radius to match specific devices:

- `ios` (default): 45px (Standard modern iPhone)
- `duo`: 55pt (iPhone Duo inner display)
- `duo-outer`: 59pt (iPhone Duo outer display)
- `ipad`: 18pt (iPad Pro 11")
- `android`: 36px (Google Pixel)
- `macos`: 16px (MacBook Screen)
- `pc`: 8px (Surface Laptop)

### Examples

**1. Process a single image with default iOS rounded corners:**

```bash
uvx appstore-mockup ./screenshot.png
```

**2. Use the Android template to match a Pixel device:**

```bash
uvx appstore-mockup ./screenshot.png --template android
```

**3. Add a glassmorphism (blurry) border and export as WEBP:**

```bash
uvx appstore-mockup ./images -t blur -s 40 -f webp -o ./dist
```

**4. Add a solid dark border with a specific corner radius:**

```bash
uvx appstore-mockup ./screenshot.png -t color -s 12 -c "#1c1c1e" -r 30
```

## Store screenshots from a layout spec

`compose` builds finished store screenshots: a gradient background, app screens in frosted glass frames with a soft shadow, and short captions. A JSON layout spec describes each screenshot as stacked elements.

```bash
uvx appstore-mockup compose ./layouts/iphone.json -o ./build/iphone
```

It writes a flattened preview per screen to `previews/`, every layer as a canvas-sized PNG to `layers/`, and a `manifest.json` describing how the layers stack. Use `--only` with screen ids to compose a subset.

```json
{
  "canvas": { "width": 1320, "height": 2868 },
  "background": {
    "direction": "to-bottom-right",
    "stops": [
      { "color": "#BCE6D5", "position": 0 },
      { "color": "#F8FAE1", "position": 1 }
    ]
  },
  "fonts": {
    "headline": { "postscript_name": "Merriweather-Bold", "file": "fonts/Merriweather-Bold.ttf" }
  },
  "source_dir": "screens",
  "screens": [
    {
      "id": "01-specimens",
      "elements": [
        { "type": "text", "text": "Every specimen,\nevery part", "font": "headline", "size": 100, "top": 0.058 },
        { "type": "device", "image": "phone.png", "radius": 92, "crop": [0, 180, 0, 0], "cy": 0.56, "max_width": 0.9, "max_height": 0.76 }
      ]
    }
  ]
}
```

- Positions (`cx`, `cy`, `top`) and boxes (`max_width`, `max_height`) are fractions of the canvas. Font `size` is in pixels.
- `text` elements are centred on `cx`, with `top` at the top of the inked text. Lines break at `\n` and wherever they exceed `max_width`. `tracking` is in thousandths of an em.
- `device` elements fit a screenshot inside their box. `crop` trims left, top, right, and bottom source pixels. `radius` sets the corner radius in source pixels; otherwise the `template` default applies. `retouch` paints out a stroke of one colour in a source box, such as the iPad screenshot-gesture mark: `{ "box": [1600, 2352, 1668, 2420], "color": "#FFFFFF" }`.
- `image` elements place a plain image, such as a logo, with optional `opacity`.
- `device` and `image` elements can set their own `source_dir`, resolved against the spec's folder, for screens kept apart from the spec's main `source_dir`, such as fresh captures.
- `frame` tunes the glass mat in CSS pixels of a 500px reference panel, scaled to the canvas: `border`, `color`, `backdrop_blur`, `hairline`, and the `shadow_*` values.
- `compose` warns when the canvas matches no size App Store Connect accepts: screenshots (including iPhone Duo inner 2007×2853 and outer 1398×2034, either orientation), the product page header (3840×1646), or a 3:2 search results image (1920×1280 to 3840×2560).
- Relative `source_dir` and font paths resolve against the spec's folder. Screenshots with an embedded colour profile, such as Display P3, are converted to sRGB.

## Photoshop masters (macOS)

`photoshop` turns a compose manifest into layered PSD masters and flattened PNG exports without transparency, ready for upload.

```bash
uvx appstore-mockup photoshop ./build/iphone/manifest.json --psd-dir ./masters --png-dir ./screenshots
```

Each device becomes a group with `Shadow`, `Glass mat`, `Screen shape`, and a `Screenshot` smart object clipped to the shape, so a new capture can be swapped in. Captions are editable text layers; the font's PostScript name must be installed for Photoshop. The command drives `Adobe Photoshop 2026` through AppleScript by default; pass `--app` for another version.

## License

MIT License.
