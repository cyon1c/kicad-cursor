# Research

One directory per selected IC: `research/<MPN>/`. Written by `@datasheet-research` after the IC is locked in `bom-targets.yaml`.

```powershell
Copy-Item -Recurse research/_template research/BQ25619LRTWR
```

| File | Purpose |
|------|---------|
| `overview.md` | What the chip does and where it sits in the system |
| `pins.md` | Pin-by-pin function, type, strapping, external parts **by role** |
| `passives-required.md` | Required/nominal passives per pin or subcircuit — values, no LCSC |
| `interfaces.md` | Optional: I²C/SPI/USB behavior, timing, sequencing |

## Rules

- Source of truth is `datasheets/extracted/<stem>/tables/*.yaml` — not raw PDFs, not screenshots. Run `extract-datasheet` first.
- Cite the extracted table or page for every spec. No guessed numbers; mark unknowns `TBD` and raise an open question.
- **No LCSC numbers here.** Passive part numbers are assigned after schematic review.
- Tiered depth: overview first, then pin groups, then deep dives on request. Full walkthroughs of high-pin-count parts exhaust context.
