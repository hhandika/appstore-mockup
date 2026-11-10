"""Rewrite msstore-screenshots.json to follow Microsoft Store screenshot guidance.

Desktop screenshots must not carry extra logos or marketing text, so captions are
dropped and the app window fills the frame. Captions go in Partner Center instead.
"""
import json
from pathlib import Path

spec_path = Path(__file__).resolve().parent.parent / "_layouts" / "msstore-screenshots.json"
spec = json.loads(spec_path.read_text())
spec.pop("fonts", None)
for screen in spec["screens"]:
    devices = [e for e in screen["elements"] if e["type"] == "device"]
    for d in devices:
        d.update(cx=0.5, cy=0.5, max_width=0.92, max_height=0.88)
    screen["elements"] = devices
spec_path.write_text(json.dumps(spec, indent=2) + "\n")
