import os
from PIL import Image, UnidentifiedImageError
from appstore_mockup.config import MockupConfig, template_radius
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
        return template_radius(self.config.template, image_width)

    def _process_single_file(self, file_path: str, output_dir: str) -> str | None:
        try:
            image = Image.open(file_path).convert("RGBA")
        except UnidentifiedImageError:
            return None
        except Exception as e:
            return None

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
        return output_path

    def process_path(self, input_path: str, output_dir: str) -> None:
        files_to_process = []
        if os.path.isfile(input_path):
            files_to_process.append(input_path)
        elif os.path.isdir(input_path):
            for root, _, files in os.walk(input_path):
                for file in files:
                    files_to_process.append(os.path.join(root, file))
        else:
            print(f"Invalid input path: {input_path}")
            return

        if not files_to_process:
            print("No files to process.")
            return

        from concurrent.futures import ThreadPoolExecutor, as_completed
        from tqdm import tqdm

        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self._process_single_file, path, output_dir): path
                for path in files_to_process
            }
            
            with tqdm(total=len(futures), desc="Processing mockups", unit="file") as pbar:
                for future in as_completed(futures):
                    # We can access future.result() if needed, but here we just update progress
                    future.result()
                    pbar.update(1)

        rel_output_dir = os.path.relpath(output_dir)
        print(f"\n✨ Successfully exported to: {rel_output_dir}")
