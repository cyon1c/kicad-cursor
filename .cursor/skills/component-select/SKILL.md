---
name: component-select
description: Select electronic components from datasheets and LCSC, match against the global KiCad library, and import missing parts via fetchPart. Use when choosing ICs, passives, connectors, or when the user mentions datasheets, LCSC, JLCPCB, or BOM parts.
---

# Component Selection

## Decision order

1. Read `bom-targets.yaml` in the active project — use listed parts if they fit
2. Search `global.kicad_sym` for existing symbols (grep by MPN or LCSC in file)
3. If missing, find LCSC part number and import via WSL
4. Validate datasheet requirements before finalizing

## Search global library

```bash
rg 'BQ25895|C80200' "C:/Users/Elli Furedy/projects/global-kicad-lib/global.kicad_sym"
```

Symbol names are typically the manufacturer MPN, not the LCSC ID.

## Import from LCSC

```bash
wsl bash -lc "fetchPart <LCSC_ID>"
wsl bash -lc "python3 '/mnt/c/Users/Elli Furedy/projects/kicad-cursor/scripts/fix-symbol-lib.py'"
```

Then add the part to the project's `bom-targets.yaml` for reuse.

## Datasheet checklist

When reading PDFs in `projects/<board>/datasheets/`:

- [ ] Supply voltage range and absolute maximums
- [ ] Typical application circuit (reference design)
- [ ] Required external components (caps, inductors, resistors)
- [ ] Pin functions and strapping requirements
- [ ] Package / footprint compatibility with `global.pretty`

Do not guess critical specs — cite the datasheet section or ask the user.

## Footprint assignment

Set schematic footprint field to `global:<footprint_name>` matching the imported footprint file in `global.pretty/`.

## Output format

When proposing a part, report:

```markdown
- **MPN**: BQ25895RTWR
- **LCSC**: C80200
- **Symbol**: global:BQ25895RTWR
- **Footprint**: global:QFN-24_L4.0-W4.0-P0.50-TL-EP2.7
- **Status**: in library | needs fetchPart
- **Rationale**: (one line from datasheet or design.yaml)
```
