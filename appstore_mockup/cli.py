import argparse
from appstore_mockup.runner import BatchRunner
from appstore_mockup.editor import ImageEditor
from appstore_mockup.exporter import ImageExporter
from appstore_mockup.config import MockupConfig

def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="App Store Mockup Generator")
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("-o", "--output-dir", default="./output", help="Output directory")
    parser.add_argument("-f", "--format", choices=["png", "webp"], default="png", help="Export format")
    parser.add_argument("-t", "--border-type", choices=["color", "blur"], default="color", help="Border type")
    parser.add_argument("-s", "--border-size", type=int, default=0, help="Border size in pixels")
    parser.add_argument("-c", "--border-color", default="#FFFFFF", help="Border color (hex or name)")
    parser.add_argument("--template", choices=["ios", "macos", "android", "pc"], default="ios", help="Device template for default rounded corners")
    parser.add_argument("-r", "--radius", type=int, default=None, help="Corner rounding radius in pixels (overrides template default)")
    return parser.parse_args(args)

def main() -> None:
    args = parse_args()
    
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

if __name__ == "__main__":
    main()
