"""Render mark.svg to a transparent PNG at a given size."""
import sys
import resvg_py

svg, out, size = sys.argv[1], sys.argv[2], int(sys.argv[3])
data = resvg_py.svg_to_bytes(svg_path=svg, width=size, height=size)
open(out, "wb").write(bytes(data))
