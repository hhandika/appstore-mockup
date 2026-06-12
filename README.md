# appstore-mockup

A Python CLI utility to automate the creation of app store mockups. It allows you to style your raw app screenshots with rounded corners, solid color borders, or glassmorphism effects, preparing them for final store listings.

## Features
- **Rounded Corners**: Emulate native device display rounding (e.g., standard iOS corners).
- **Glass Borders**: Add a sleek, glass-like frosted border around your screenshots.
- **Color Borders**: Add crisp, solid color borders.
- **Batch Processing**: Process a single image or an entire directory of screenshots.
- **Transparent Exports**: Export directly to PNG or lossless WEBP with a transparent canvas.

## Installation

This tool uses [uv](https://github.com/astral-sh/uv). Install it globally:

```bash
uv tool install appstore-mockup
```

Alternatively, you can run it directly without prior installation:

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
| `--template` | Device template for default corner radius (`ios`, `macos`, `android`, `pc`). | `ios` |
| `-s`, `--border-size` | Width of the outer border in pixels. | `0` |
| `-c`, `--border-color` | Hex or RGB color code for `color` border type. | `#FFFFFF` |
| `-r`, `--radius` | Corner rounding radius in pixels (overrides template). | template default |

### Templates
The `--template` option sets the default corner rounding radius to match specific devices:
- `ios` (default): 45px (Standard modern iPhone)
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

## License

MIT License.
