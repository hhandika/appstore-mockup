"""Append the read report plot screens to msstore-screenshots.json."""
import json
from pathlib import Path

spec_path = Path(__file__).resolve().parent.parent / "_layouts" / "msstore-screenshots.json"
spec = json.loads(spec_path.read_text())
template = spec["screens"][0]["elements"][0]
existing = {s["id"] for s in spec["screens"]}
for sid, image in [("09-read-quality", "read-report-quality-large.png"),
                   ("10-read-composition", "read-report-composition-large.png")]:
    if sid in existing:
        continue
    spec["screens"].append({"id": sid, "elements": [dict(template, image=image)]})
spec_path.write_text(json.dumps(spec, indent=2) + "\n")
print([s["id"] for s in spec["screens"]])
