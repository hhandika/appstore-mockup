import os
from PIL import Image, UnidentifiedImageError
from appstore_mockup.editor import apply_rounded_corners, apply_color_border, apply_glass_border
from appstore_mockup.exporter import export_image

def process_single_file(file_path: str, output_dir: str, config: dict) -> None:
    try:
        image = Image.open(file_path).convert("RGBA")
    except UnidentifiedImageError:
        return
    except Exception as e:
        print(f"Error opening {file_path}: {e}")
        return

    radius = config.get("radius", 45)
    border_size = config.get("border_size", 0)
    border_type = config.get("border_type", "color")
    border_color = config.get("border_color", "#FFFFFF")
    fmt = config.get("format", "png")

    image = apply_rounded_corners(image, radius)

    if border_type == "blur":
        image = apply_glass_border(image, border_size, radius)
    else:
        image = apply_color_border(image, border_size, border_color, radius)

    filename = os.path.basename(file_path)
    name, _ = os.path.splitext(filename)
    output_path = os.path.join(output_dir, f"{name}.{fmt}")
    
    export_image(image, output_path, fmt)
    print(f"Exported: {output_path}")

def process_path(input_path: str, output_dir: str, config: dict) -> None:
    if os.path.isfile(input_path):
        process_single_file(input_path, output_dir, config)
    elif os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            for file in files:
                file_path = os.path.join(root, file)
                process_single_file(file_path, output_dir, config)
    else:
        print(f"Invalid input path: {input_path}")
