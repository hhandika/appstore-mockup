"""Build layered Photoshop masters from a compose manifest."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

JSX_PATH = Path(__file__).parent / "jsx" / "build_masters.jsx"
DEFAULT_APP = "Adobe Photoshop 2026"


class PhotoshopBuilder:
    """Drives Photoshop through AppleScript to run the master-building script."""

    def __init__(self, app: str = DEFAULT_APP, timeout: int = 7200):
        self.app = app
        self.timeout = timeout

    def build(
        self,
        manifest: str | Path,
        psd_dir: str | Path,
        png_dir: str | Path,
        only: list[str] | None = None,
    ) -> str:
        """Saves one PSD and one flattened PNG per manifest screen."""
        if sys.platform != "darwin":
            raise RuntimeError("Photoshop automation is only supported on macOS.")
        job = {
            "manifest": str(Path(manifest).absolute()),
            "psd_dir": Path(psd_dir).absolute().as_posix(),
            "png_dir": Path(png_dir).absolute().as_posix(),
            "only": only or [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            job_path = Path(temp_dir) / "job.json"
            job_path.write_text(json.dumps(job), encoding="utf-8")
            result = subprocess.run(
                ["osascript", "-e", self.applescript(job_path)],
                capture_output=True,
                text=True,
            )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Photoshop script failed.")
        return result.stdout.strip()

    def applescript(self, job_path: Path) -> str:
        script = _quote(str(JSX_PATH))
        job = _quote(str(job_path))
        return (
            f"with timeout of {self.timeout} seconds\n"
            f'tell application "{_quote(self.app)}" to do javascript '
            f'(read (POSIX file "{script}") as «class utf8») with arguments {{"{job}"}}\n'
            "end timeout"
        )


def _quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
