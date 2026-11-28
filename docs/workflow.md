# Schematic design workflow

The short guide. **You draw the schematic; the agent does everything around it.** For the full rationale, roles, and prior art, see [workflow-plan.md](workflow-plan.md).

## The three rules

1. **You draw.** Agents never place, wire, or modify `.kicad_sch`. Konnect is read-only for schematics — design context and JLC lookup only.
2. **ICs before passives.** ICs get LCSC numbers up front. Passives get a *value field* while you draw, and LCSC numbers only after review.
3. **Review includes ERC.** A schematic review that did not run ERC is not finished.

## Six phases

| # | Phase | Skill | You get |
|---|-------|-------|---------|
| 1 | Design consultation | `/kicad:design-consultant` | `design.yaml`, `constraints.md`, `design-log/architecture.md`, IC intent per block |
| 2 | IC intake | `/kicad:component-select` (mode A) | LCSC + `fetch-part` for ICs, `bom-targets.yaml` `ic-locked`, `design-log/ic-selection.md` |
| 3 | Datasheet research | `/kicad:datasheet-research` | `research/<MPN>/` — overview, pins, required passives with values |
| 4 | **You draw the schematic** | `/kicad:schematic-draw` | Per-block drawing briefs: symbols, nets, values, gotchas |
| 5 | Schematic review | `/kicad:schematic-review` | Context dump + ERC + value audit + intent diff → `design-log/reviews/<date>.md` |
| 6 | Passive finalize | `/kicad:component-select` (mode B) | LCSC per passive value, `passive-locked`, `design-log/passive-bom.md` |

`design-log/` gets appended at every phase. Run **one skill per session** — mixing roles is how the agent starts picking parts during a review.

## Walking through it

### 1. Consultation

```text
/kicad:design-consultant — 1S Li-ion, USB-C in, 3.3V rail for an ESP32-S3, 60x40mm
```

The agent asks for load currents, battery details, and interfaces, then writes the power tree and block list. Anything it had to assume becomes an open question with your name on it.

### 2. IC intake

```text
/kicad:component-select IC mode for the charger and regulator
```

LCSC numbers, stock check, `fetch-part` into your symbol library, `bom-targets.yaml` at `status: ic-locked`. Passives are not touched here.

### 3. Research

Drop the datasheet PDF in `<projectDir>/datasheets/`, then:

```powershell
kicad-step extract-datasheet --pdf datasheets/bq25619.pdf
```

```text
/kicad:datasheet-research BQ25619
```

You get `research/BQ25619/pins.md` and `passives-required.md` — pin functions, what must not float, and every required passive with a value and a critical flag. The agent reads `datasheets/extracted/<stem>/tables/*.yaml`, not the raw PDF.

### 4. Draw

```text
/kicad:schematic-draw — drawing brief for the regulation block
```

Then draw it in KiCad. While drawing:

- Every passive gets a **value** (`100nF`, `10k`, `0.01Ω`) — no empty fields
- Passive LCSC numbers are **not** needed yet
- ICs use `global:<MPN>` symbols
- Net names uppercase with underscores, matching `design.yaml` rails
- `PWR_FLAG` on source nets
- **Ctrl+S** before asking for a review

### 5. Review

```text
/kicad:schematic-review — full design
```

The agent dumps fresh context, runs ERC, audits every passive value, diffs the sheet against your architecture and research, and writes a report with a gate verdict.

```powershell
kicad-step dump-design-context
kicad-step verify-erc
```

Blockers come back as instructions for you; the agent does not fix the sheet.

### 6. Passive finalize

```text
/kicad:component-select passive mode
```

Only after review passes. One LCSC per value/package group, ratings per `constraints.md`, `bom-targets.yaml` moves to `passive-locked`.

## Gate before the passive pass

- [ ] Blocking open questions resolved or explicitly deferred
- [ ] ICs on the sheet match `bom-targets.yaml` / `ic-selection.md`
- [ ] `dump-design-context` run on the **saved** schematic (timestamp logged)
- [ ] ERC run; errors fixed or waived with rationale
- [ ] Every passive ref has a value field
- [ ] Critical passives match `research/*/passives-required.md`

## Files in your project

```text
my-board/
  design.yaml          constraints.md       bom-targets.yaml
  datasheets/          research/<MPN>/      design-log/
  design-context/      # generated — do not hand-edit
```

Start from [examples/kicad-project-template](../examples/kicad-project-template/README.md); each file's owner is listed in its README.

## Other skills

| Skill | Use |
|-------|-----|
| `/kicad:kicad-project` | Config, library paths, project conventions |
| `/kicad:kicad-step` | Run one cataloged script ([steps.md](steps.md)) |
| `/kicad:konnect` | JLC lookup and read-only context via MCP |
| `/kicad:design-verify` | Ad-hoc ERC/DRC outside a formal review |
| `/kicad:design-log` | Append decisions, or catch up on an unfamiliar board |

## PCB layout — deferred

The layout phase is not defined yet. Placement and routing roles, Konnect PCB toolsets, and a DRC gate come after the schematic workflow is stable ([workflow-plan.md](workflow-plan.md) §7 Deferred). Until then `/kicad:pcb-layout` holds starting-point guidance only, and layout should not begin until a schematic has passed review with passives locked.
