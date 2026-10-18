# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `compose` subcommand that builds store screenshots from a JSON layout spec: gradient backgrounds, frosted glass device frames with drop shadows, captions, and plain images.
- Compose writes flattened previews, per-layer PNGs, and a layer manifest.
- `retouch` option that paints out a stroke of one colour, such as the iPad screenshot-gesture mark.
- Per-element `source_dir` for device and image elements.
- `photoshop` subcommand that builds layered PSD masters, with smart-object screenshots and editable captions, and flattened PNG exports (macOS).
- `ipad` corner radius template.
- `duo` and `duo-outer` corner radius templates for the iPhone Duo inner and outer displays.
- `compose` warns when a canvas matches no App Store screenshot, product page header, or search results size.

### Changed
- Screenshots with an embedded colour profile are converted to sRGB when composed.

## [0.1.0] - 2026-06-11

### Added
- Initial release of the `appstore-mockup` CLI tool to PyPI.
- Apply rounded corners based on device templates (`ios`, `android`, `macos`, `pc`) or custom radius.
- Add sleek glassmorphism (blurry) borders or solid color borders to screenshots.
- Batch process entire directories or individual images.
- Export results as PNG or lossless WEBP with transparent backgrounds.
