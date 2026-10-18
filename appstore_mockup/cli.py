import argparse
import sys
from appstore_mockup.runner import BatchRunner
from appstore_mockup.editor import ImageEditor
from appstore_mockup.exporter import ImageExporter
from appstore_mockup.config import MockupConfig, TEMPLATE_RADII
from appstore_mockup.layout import LayoutSpec
from appstore_mockup.compose import ScreenComposer
from appstore_mockup.stores import check_canvas
from appstore_mockup.photoshop import DEFAULT_APP, PhotoshopBuilder

def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="App Store Mockup Generator",
        epilog="Subcommands: 'compose SPEC' builds store screenshots from a layout spec; "
        "'photoshop MANIFEST' builds layered PSD masters from its manifest.",
    )
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("-o", "--output-dir", default="./output", help="Output directory")
    parser.add_argument("-f", "--format", choices=["png", "webp"], default="png", help="Export format")
    parser.add_argument("-t", "--border-type", choices=["color", "blur"], default="color", help="Border type")
    parser.add_argument("-s", "--border-size", type=int, default=0, help="Border size in pixels")
    parser.add_argument("-c", "--border-color", default="#FFFFFF", help="Border color (hex or name)")
    parser.add_argument("--template", choices=list(TEMPLATE_RADII), default="ios", help="Device template for default rounded corners")
    parser.add_argument("-r", "--radius", type=int, default=None, help="Corner rounding radius in pixels (overrides template default)")
    return parser.parse_args(args)

def parse_compose_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="appstore-mockup compose",
        description="Compose framed store screenshots, layers, and a manifest from a layout spec",
    )
    parser.add_argument("spec", help="Layout spec JSON file")
    parser.add_argument("-o", "--output-dir", default="./output", help="Output directory")
    parser.add_argument("--only", nargs="+", default=None, help="Screen ids to compose")
    return parser.parse_args(args)

def parse_photoshop_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="appstore-mockup photoshop",
        description="Build layered PSD masters and flattened PNGs from a compose manifest (macOS)",
    )
    parser.add_argument("manifest", help="manifest.json written by the compose command")
    parser.add_argument("--psd-dir", required=True, help="Directory for PSD masters")
    parser.add_argument("--png-dir", required=True, help="Directory for flattened PNG exports")
    parser.add_argument("--app", default=DEFAULT_APP, help="Photoshop application name")
    parser.add_argument("--only", nargs="+", default=None, help="Screen ids to build")
    return parser.parse_args(args)

def run_mockup(args: argparse.Namespace) -> None:
    config = MockupConfig(
        format=args.format,
        border_type=args.border_type,
        border_size=args.border_size,
        border_color=args.border_color,
        radius=args.radius,
        template=args.template,
    )

    editor = ImageEditor()
    exporter = ImageExporter()
    runner = BatchRunner(config, editor, exporter)
    runner.process_path(args.input, args.output_dir)

def run_compose(args: argparse.Namespace) -> None:
    spec = LayoutSpec.load(args.spec)
    warning = check_canvas(spec.canvas.width, spec.canvas.height)
    if warning:
        print(f"⚠️  {warning}")
    manifest = ScreenComposer(spec).compose_all(args.output_dir, args.only)
    print(f"✨ Composed screens. Manifest: {manifest}")

def run_photoshop(args: argparse.Namespace) -> None:
    builder = PhotoshopBuilder(app=args.app)
    print(builder.build(args.manifest, args.psd_dir, args.png_dir, args.only))

def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "compose":
        run_compose(parse_compose_args(argv[1:]))
    elif argv and argv[0] == "photoshop":
        run_photoshop(parse_photoshop_args(argv[1:]))
    else:
        run_mockup(parse_args(argv))

if __name__ == "__main__":
    main()
