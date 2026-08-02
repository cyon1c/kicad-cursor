---
name: design-verify
description: Run KiCad ERC and DRC checks and interpret results before marking design work complete. Use after schematic or PCB changes, or when the user asks to validate, verify, or check a design.
---

# Design Verification

## Gate rule

**Do not mark schematic or PCB work as complete until ERC/DRC have been run and results are reported.**

If violations remain, list them and either fix or explain why they are acceptable.

## Schematic ERC

```powershell
& "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" sch erc "projects/<board>/<board>.kicad_sch"
```

Or use MCP schematic tools if available.

Common ERC issues:

- Unconnected pins
- Power pin not driven
- Duplicate references
- Footprint not assigned

## PCB DRC

```powershell
& "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb drc "projects/<board>/<board>.kicad_pcb"
```

Common DRC issues:

- Clearance violations
- Unrouted nets
- Courtyard overlaps
- Silkscreen over pads

## Symbol library health

After `fetchPart`:

```powershell
python scripts/fix-symbol-lib.py --check
```

If exit code 1, run without `--check` to repair, then restart KiCad.

## Report format

```markdown
## Verification: <board-name>

### ERC
- Status: PASS | FAIL (N violations)
- (list violations or "clean")

### DRC
- Status: PASS | FAIL (N violations)
- (list violations or "clean")

### Library
- global.kicad_sym: OK | repaired

### Ready for next step
- Yes / No — (reason)
```
