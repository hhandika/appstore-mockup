import argparse
from appstore_mockup.runner import process_path

def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="App Store Mockup Generator")
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("-o", "--output-dir", default="./output", help="Output directory")
    parser.add_argument("-f", "--format", choices=["png", "webp"], default="png", help="Export format")
    parser.add_argument("-t", "--border-type", choices=["color", "blur"], default="color", help="Border type")
    parser.add_argument("-s", "--border-size", type=int, default=0, help="Border size in pixels")
    parser.add_argument("-c", "--border-color", default="#FFFFFF", help="Border color (hex or name)")
    parser.add_argument("-r", "--radius", type=int, default=45, help="Corner rounding radius in pixels")
    return parser.parse_args(args)

def main() -> None:
    args = parse_args()
    config = {
        "format": args.format,
        "border_type": args.border_type,
        "border_size": args.border_size,
        "border_color": args.border_color,
        "radius": args.radius,
    }
    process_path(args.input, args.output_dir, config)

if __name__ == "__main__":
    main()
