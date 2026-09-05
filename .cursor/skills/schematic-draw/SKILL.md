---
name: schematic-draw
description: Guidance and checklists for the human drawing a KiCad schematic block by hand — what to place, how to wire it, value fields, net naming. Use when the user is about to draw or is mid-draw on a block and wants direction. The agent never places or wires anything.
---

# Schematic drawing guidance (human draws)

The agent's job here is to **tell the user what to draw**, then get out of the way. No `.kicad_sch` edits, no Konnect placement tools, no ERC (that belongs to `@schematic-review`).

## Inputs before advising

1. `<projectDir>/design.yaml` — rails, blocks, `openQuestions`
2. `<projectDir>/constraints.md` — net naming, decoupling, value-field rules
3. `<projectDir>/research/<mpn>/pins.md` + `passives-required.md` — per-IC truth
4. `<projectDir>/bom-targets.yaml` — which symbols are already in the library

If `research/<mpn>/` is missing for the block's IC, run `@datasheet-research` first — do not improvise pin advice.

## Per-block drawing brief

Give the user one block at a time, in this shape:

```markdown
### Block: <id> — drawing brief

**Symbols to place**
- U1 `global:<MPN>` — from bom-targets (status: ic-locked)
- C1, C2 `global:C0402` — values below
- R1 `global:R0402` — value below

**Nets**
- VBUS → U1.VIN, C1.1
- GND → U1.GND, C1.2, C2.2
- I2C_SDA → U1.SDA, R1.1  (label, crosses to mcu sheet)

**Values (required before review)**
| Ref | Value | Role | Source |
|-----|-------|------|--------|
| C1 | 10µF | VIN bulk | research/<MPN>/passives-required.md |
| R1 | 4.7k | SDA pull-up | constraints.md |

**Watch out**
- <strapping pin, sequencing, or polarity note from pins.md>
```

## Drawing rules the user should follow

- **Every passive gets a value field** (`100nF`, `10k`, `0.01Ω`). `TBD` is only acceptable on non-critical nets and will be flagged at review.
- Passive **LCSC numbers are not needed yet** — they are assigned after review by `@component-select` passive mode.
- ICs use `global:<MPN>` symbols already imported into the library.
- Net names: uppercase with underscores (`V3V3`, `I2C_SDA`, `ESP32_EN`); match rail names in `design.yaml`.
- Power symbols per rail; one GND style per sheet; `PWR_FLAG` on every source net.
- One functional block per hierarchical sheet when `design.yaml` lists multiple blocks; hierarchical labels for sheet ports.
- Reference designators: `U` ICs, `R` resistors, `C` capacitors, `L` inductors, `D` diodes, `Q` transistors, `J` connectors.

## Common minimums

| Block | Minimum parts |
|-------|---------------|
| IC power pin | 100 nF close to the pin, per pin |
| IC cluster rail | Bulk 4.7–10 µF |
| LDO | 1 µF + 100 nF in, 10 µF + 100 nF out |
| Buck / boost | Input cap, output cap, inductor per datasheet |
| I²C bus | 4.7 kΩ pull-ups to the bus rail (if not internal) |
| Reset / EN | Pull-up, optional button to GND |

Datasheet-specific values always beat this table.

## Hand-off checklist (before `@schematic-review`)

- [ ] All symbols for the block placed, refs annotated (no `?`)
- [ ] Every passive has a value field
- [ ] Rails and GND connected; `PWR_FLAG` on sources
- [ ] Cross-sheet signals labeled consistently
- [ ] Strapping / config pins set per `research/<mpn>/pins.md`
- [ ] **Saved in KiCad (Ctrl+S)** — review reads the file on disk

Then hand off: `@schematic-review`.

## Will not

- Place, wire, or annotate anything in `.kicad_sch`
- Run ERC (`@schematic-review` or `@design-verify`)
- Pick passive LCSC numbers (`@component-select` passive mode)
- Re-architect the block (`@design-consultant`)
