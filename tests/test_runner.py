import os
import pytest
from PIL import Image
from appstore_mockup.runner import BatchRunner
from appstore_mockup.editor import ImageEditor
from appstore_mockup.exporter import ImageExporter
from appstore_mockup.config import MockupConfig

@pytest.fixture
def temp_workspace(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    img1 = Image.new("RGBA", (100, 100), color="blue")
    img1.save(input_dir / "img1.png")
    
    img2 = Image.new("RGBA", (200, 200), color="red")
    img2.save(input_dir / "img2.png")
    
    (input_dir / "not_an_image.txt").write_text("hello")
    
    return {
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "img1_path": str(input_dir / "img1.png")
    }

def get_runner(config: MockupConfig) -> BatchRunner:
    return BatchRunner(config, ImageEditor(), ImageExporter())

def test_process_single_file(temp_workspace):
    config = MockupConfig(
        format="png",
        border_type="color",
        border_size=10,
        border_color="#FFFFFF",
        radius=10,
    )
    
    runner = get_runner(config)
    runner.process_path(temp_workspace["img1_path"], temp_workspace["output_dir"])
    
    out_file = os.path.join(temp_workspace["output_dir"], "img1.png")
    assert os.path.exists(out_file)
    
    out_img = Image.open(out_file)
    assert out_img.size == (120, 120)

def test_process_directory(temp_workspace):
    config = MockupConfig(
        format="webp",
        border_type="blur",
        border_size=20,
        radius=15,
    )
    
    runner = get_runner(config)
    runner.process_path(temp_workspace["input_dir"], temp_workspace["output_dir"])
    
    assert os.path.exists(os.path.join(temp_workspace["output_dir"], "img1.webp"))
    assert os.path.exists(os.path.join(temp_workspace["output_dir"], "img2.webp"))
    assert not os.path.exists(os.path.join(temp_workspace["output_dir"], "not_an_image.webp"))

def test_template_dynamic_radius(temp_workspace):
    config = MockupConfig(
        format="png",
        border_type="color",
        border_size=10,
        template="ios",
        radius=None,
    )
    
    runner = get_runner(config)
    runner.process_path(temp_workspace["img1_path"], temp_workspace["output_dir"])
    
    out_file = os.path.join(temp_workspace["output_dir"], "img1.png")
    assert os.path.exists(out_file)
    out_img = Image.open(out_file)
    assert out_img.size == (120, 120)
