"""Draw a rectangular board outline on Edge.Cuts via KiCad IPC API."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from kicad_cursor_config import addProjectArgs, resolveProjectDir
from kipy import KiCad
from kipy.board_types import BoardSegment
from kipy.geometry import Vector2
from kipy.proto.board.board_types_pb2 import BoardLayer
from kipy.util import from_mm


def loadBoardSizeMm(projectDir: Path) -> tuple[float, float]:
    designFile = projectDir / "design.yaml"
    if designFile.is_file():
        data = yaml.safe_load(designFile.read_text(encoding="utf-8"))
        size = data.get("constraints", {}).get("boardSizeMm", [50, 50])
        return float(size[0]), float(size[1])
    return 50.0, 50.0


def makeEdgeSegment(x1: float, y1: float, x2: float, y2: float, widthMm: float) -> BoardSegment:
    segment = BoardSegment()
    segment.layer = BoardLayer.BL_Edge_Cuts
    segment.start = Vector2.from_xy_mm(x1, y1)
    segment.end = Vector2.from_xy_mm(x2, y2)
    segment.attributes.stroke.width = from_mm(widthMm)
    return segment


def rectangleOutline(widthMm: float, heightMm: float, lineWidthMm: float = 0.1) -> list[BoardSegment]:
    return [
        makeEdgeSegment(0, 0, widthMm, 0, lineWidthMm),
        makeEdgeSegment(widthMm, 0, widthMm, heightMm, lineWidthMm),
        makeEdgeSegment(widthMm, heightMm, 0, heightMm, lineWidthMm),
        makeEdgeSegment(0, heightMm, 0, 0, lineWidthMm),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    addProjectArgs(parser)
    parser.add_argument("--width-mm", type=float, help="Override board width")
    parser.add_argument("--height-mm", type=float, help="Override board height")
    args = parser.parse_args()

    try:
        projectDir = resolveProjectDir(args.project_dir, args.project)
    except (FileNotFoundError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 2

    widthMm, heightMm = loadBoardSizeMm(projectDir)
    if args.width_mm is not None:
        widthMm = args.width_mm
    if args.height_mm is not None:
        heightMm = args.height_mm

    print(f"outline: {widthMm} x {heightMm} mm (project: {projectDir})")

    kicad = KiCad()
    board = kicad.get_board()
    segments = rectangleOutline(widthMm, heightMm)
    board.create_items(segments)
    print(f"OK: drew {len(segments)} Edge.Cuts segments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
