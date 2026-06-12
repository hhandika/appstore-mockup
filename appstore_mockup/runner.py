import os
from PIL import Image, UnidentifiedImageError
from appstore_mockup.config import MockupConfig
from appstore_mockup.editor import ImageEditor
from appstore_mockup.exporter import ImageExporter

class BatchRunner:
    def __init__(self, config: MockupConfig, editor: ImageEditor, exporter: ImageExporter):
        self.config = config
        self.editor = editor
        self.exporter = exporter

    def _calculate_radius(self, image_width: int) -> int:
        if self.config.radius is not None:
            return self.config.radius
            
        templates = {
            "ios": (47.33, 393),       # iPhone 15 Pro
            "android": (36, 412),      # Pixel 8
            "macos": (16, 1440),       # MacBook Pro
            "pc": (8, 1504),           # Surface Laptop
        }
        pts, logical_width = templates.get(self.config.template, templates["ios"])
        return int(image_width * (pts / logical_width))

    def _process_single_file(self, file_path: str, output_dir: str) -> None:
        try:
            image = Image.open(file_path).convert("RGBA")
        except UnidentifiedImageError:
            return
        except Exception as e:
            print(f"Error opening {file_path}: {e}")
            return

        radius = self._calculate_radius(image.width)
        
        image = self.editor.apply_rounded_corners(image, radius)

        if self.config.border_type == "blur":
            image = self.editor.apply_glass_border(image, self.config.border_size, radius)
        else:
            image = self.editor.apply_color_border(image, self.config.border_size, self.config.border_color, radius)

        filename = os.path.basename(file_path)
        name, _ = os.path.splitext(filename)
        output_path = os.path.join(output_dir, f"{name}.{self.config.format}")
        
        self.exporter.export(image, output_path, self.config.format)
        print(f"Exported: {output_path}")

    def process_path(self, input_path: str, output_dir: str) -> None:
        if os.path.isfile(input_path):
            self._process_single_file(input_path, output_dir)
        elif os.path.isdir(input_path):
            for root, _, files in os.walk(input_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    self._process_single_file(file_path, output_dir)
        else:
            print(f"Invalid input path: {input_path}")
