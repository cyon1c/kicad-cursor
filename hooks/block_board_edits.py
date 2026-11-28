"""PreToolUse hook: the user draws schematics and boards; agents never edit KiCad design files.

Blocks Edit/Write on .kicad_sch, .kicad_pcb and .kicad_pro. Exit code 2 = block, and stderr is shown to Claude.
Stdlib only.
"""

import json
import sys

PROTECTED = (".kicad_sch", ".kicad_pcb", ".kicad_pro")


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    path = str((event.get("tool_input") or {}).get("file_path") or (event.get("tool_input") or {}).get("notebook_path") or "")
    if path.lower().endswith(PROTECTED):
        print(
            f"Blocked by the kicad plugin: agents never edit KiCad design files ({path}). "
            "The user draws schematics and boards in KiCad; write a drawing brief (/kicad:schematic-draw) "
            "or a review finding instead.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
