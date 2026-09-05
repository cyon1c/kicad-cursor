---
name: datasheet-research
description: Deep per-IC research from extracted datasheets — features, pin-by-pin function, strapping, required passives by role, interfaces. Use after an IC is selected, so the user can draw its schematic correctly. Does not assign LCSC numbers or edit schematics.
---

# Schematic Research Assistant

One selected IC at a time. Produce `research/<MPN>/` that the user draws from and `@schematic-review` diffs against.

## Prerequisite: extract the PDF

The user drops the PDF in `<projectDir>/datasheets/`. Then:

```powershell
uv run python scripts/run_step.py extract-datasheet --pdf datasheets/<file>.pdf
```

Output lands in `<projectDir>/datasheets/extracted/<pdf-stem>/`:

```text
index.md      manifest.yaml
tables/       # ← specs come from here (YAML)
pages/        # prose, features, application notes
images/       # pinout and application circuit figures
```

**Read `tables/*.yaml` for numbers.** Do not re-read the raw PDF, do not trust markdown pipe tables in `pages/`, do not ask for screenshots.

## Read first

- `datasheets/extracted/<stem>/index.md` — then only the tables and pages you need
- `design.yaml` rails and the block this IC serves
- `design-log/architecture.md` — the rails and signals this chip must interface with
- `design-log/ic-selection.md` — why this part was chosen

## Write to `research/<MPN>/`

Copy the template, then fill it:

```powershell
Copy-Item -Recurse examples/kicad-project-template/research/_template <projectDir>/research/<MPN>
```

```bash
cp -R examples/kicad-project-template/research/_template <projectDir>/research/<MPN>
```

| File | Content |
|------|---------|
| `overview.md` | Chip's job in one paragraph, key specs with sources, where it sits, which app figure applies |
| `pins.md` | Pin table (function, type, strapping, external parts **by role**), pin groups, app circuit decoded, path to next IC |
| `passives-required.md` | Required/nominal passives per pin or subcircuit, tolerance, **critical? flag**, calculated values with equations |
| `interfaces.md` | Optional — bus, addresses, sequencing, timing, interrupt idle states |

## Walkthrough order (tiered — stop at each tier unless asked for more)

1. **Overview** — what the chip does, one paragraph
2. **Pin groups** — power pins, ground/thermal, control/strapping, functional groups (all LED sinks, all switching nodes) described once
3. **Pin-by-pin** — only for the pins that need it, noting how each external passive influences the pin
4. **Application circuit decoded** — walk the datasheet's typical application figure against the pin table; every component in the figure gets a pin and a reason
5. **Path from IC to IC** — how rails and signals leave this chip and reach the next block

A 36-channel driver gets groups, not 36 narratives. Deep dives on request.

## Rules

- Cite the extracted table or page for every spec. Unknown stays `TBD` plus an open question — never a guess.
- Passives are named **by role and value** (`10µF VIN bulk`), never by LCSC.
- Mark `critical: yes` for anything that sets a voltage, current limit, timing, or strapping state. Review blocks on those being `TBD`.
- Show the equation and inputs for any calculated value so a reviewer can re-derive it.
- Note every pin that must not float.
- Append a `decisions.md` bullet for anything that changes design understanding.

## Will not

- Assign LCSC or run `fetch-part` → `@component-select`
- Lock passive BOM entries → `@component-select` passive mode, after review
- Edit schematics or advise placement coordinates → `@schematic-draw` writes the drawing brief
- Run ERC → `@schematic-review`

## Session summary format

```markdown
## Research: <MPN>

**Written:** research/<MPN>/{overview,pins,passives-required}.md

**Critical passives** (must not be TBD)
| Role | Pin | Value | Tol | Source |
|------|-----|-------|-----|--------|

**Must not float:** EN (pull-up), CE (strap low)

**Open questions raised**
- <question> → design-log/open-questions.md

**Next:** `@schematic-draw` for block <id>
```
