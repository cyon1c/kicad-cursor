# PCB / schematic constraints

Board-specific rules. Agents read this file before advising, reviewing, or selecting parts.

## Board

- Default 2-layer unless `design.yaml` says otherwise
- Board outline defined in the PCB editor
- Keep mounting holes ≥ 3.2 mm drill unless specified

## Who does what

- **The user draws the schematic.** Agents never edit `.kicad_sch`.
- Agents supply intent (`design.yaml`), research (`research/<mpn>/`), part identity (`bom-targets.yaml`), and reviews.
- Save in KiCad (Ctrl+S) before asking for a review — context dumps and ERC read the file on disk.

## Schematic

- Use `global:` library symbols for ICs and LCSC parts
- Net names: uppercase with underscores (`V3V3`, `I2C_SDA`, `ESP32_EN`); rail names must match `design.yaml`
- One GND symbol style per sheet; tie all grounds
- `PWR_FLAG` on every power source net
- One functional block per hierarchical sheet when `design.yaml` lists multiple blocks
- Decoupling: 100 nF per IC power pin, within 3 mm on the PCB (0402 default)
- Bulk cap 4.7–10 µF per rail near the regulator output
- Reference designators: `U` ICs, `R` resistors, `C` capacitors, `L` inductors, `D` diodes, `Q` transistors, `J` connectors

## Value fields (required before review)

- **Every passive on the sheet has a value field** — `100nF`, `10k`, `0.01Ω`. No empty values.
- `TBD` is tolerated only on non-critical nets and is reported as a warning.
- **Critical passives may not be `TBD`:** anything setting a voltage, current limit, timing, or strapping state — feedback dividers, sense resistors, ILIM/programming resistors, crystal loads, NTC networks.
- Critical values must match `research/<mpn>/passives-required.md`, including tolerance.
- Passive **LCSC numbers are not required while drawing** — they are assigned after review.

## Part selection order

1. `@design-consultant` locks architecture and IC intent
2. `@component-select` IC mode: LCSC + `fetch-part` for ICs only → `status: ic-locked`
3. `@datasheet-research`: `research/<mpn>/` with passive roles and values
4. User draws the schematic with value fields → `status: value-only`
5. `@schematic-review` signs off
6. `@component-select` passive mode: LCSC for passives → `status: passive-locked`

## Footprints

- Footprint field format: `global:<footprint_name>`
- After `fetch-part`, verify the symbol library file is valid (`fix-symbol-lib` step)

## Review gate

A schematic review is complete only when all of these hold:

- [ ] Blocking `openQuestions` in `design.yaml` / `design-log/open-questions.md` resolved or explicitly deferred
- [ ] All ICs on the sheet match `bom-targets.yaml` and `design-log/ic-selection.md`
- [ ] `dump-design-context` run against the **saved** schematic; timestamp logged in `design-log/context-snapshots.md`
- [ ] ERC run; errors fixed or waived with written rationale
- [ ] Every passive ref has a value field
- [ ] Critical passives match `research/*/passives-required.md`

ERC is mandatory in a formal review. DRC is optional during the schematic phase.

## KiCad paths

- KiCad 10 config: `%APPDATA%/kicad/10.0/` (Windows), `~/Library/Preferences/kicad/10.0/` (macOS), `~/.config/kicad/10.0/` (Linux)
- Set the `GLOBAL` KiCad env var to your shared symbol/footprint library root
- CLI: `kicad-cli` from KiCad 10 — found on PATH, or set `kicadCli` in `kicad-cursor.yaml`
