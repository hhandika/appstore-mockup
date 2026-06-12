import os
from PIL import Image

class ImageExporter:
    @staticmethod
    def export(image: Image.Image, output_path: str, fmt: str) -> None:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        save_kwargs = {}
        if fmt.lower() == "webp":
            save_kwargs["lossless"] = True
        image.save(output_path, format=fmt, **save_kwargs)
