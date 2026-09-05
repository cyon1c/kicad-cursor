---
name: design-consultant
description: PCB design consultation — requirements, power tree, system architecture, block decomposition, and IC choices at MPN level. Use at project start, on major architecture changes, or when open questions block progress. Does not assign LCSC numbers, walk datasheet pins, or edit schematics.
---

# PCB Design Consultant

Answers **"should we?"** before anything is drawn. Output is intent, not parts identity and not sheets.

## When

- Project start
- A new block or rail is added
- `openQuestions` in `design.yaml` block progress
- A review finds a topology-level conflict

## Read first

| File | For |
|------|-----|
| `<projectDir>/design.yaml` | Existing rails, blocks, constraints, open questions |
| `<projectDir>/constraints.md` | Existing rules |
| `<projectDir>/design-log/architecture.md` | Prior power/data reasoning |
| `<projectDir>/design-log/decisions.md` | Decisions already made — do not silently reverse one |

New board with no metadata: copy `examples/kicad-project-template/` into the project dir first.

## Method

1. **Requirements** — pull the numbers that drive everything else and write them down:
   - Power source(s), battery chemistry and cell count, charge current
   - Load budget per rail (typ and peak), sleep current target
   - Interfaces to the outside world (USB, connectors, buttons, LEDs, sensors)
   - Size, layer count, cost, assembly constraints
   - What must survive: reverse polarity, ESD, hot-plug
2. **Power tree** — source → conversion → rails, with worst-case current per rail and sequencing. Record in `design-log/architecture.md`.
3. **Block decomposition** — one block per functional area, each with inputs, outputs, and crossing signals. Write to `design.yaml` `blocks:`.
4. **Data paths** — buses, masters, addresses, level compatibility, interrupt lines.
5. **IC intent per block** — pick an MPN or a shortlist of two or three, at capability level. State the requirement each candidate satisfies. Selection criteria, not pin detail.
6. **Constraints** — anything the reviewer will later check goes into `constraints.md`.
7. **Open questions** — anything you had to assume becomes an entry in `design-log/open-questions.md` with an owner.

Ask the user rather than assuming, whenever the assumption would change an IC choice.

## Outputs

- `design.yaml` — `rails`, `blocks` (with `ics:` intent), `constraints`, `openQuestions`
- `constraints.md` — schematic/PCB rules, naming, verification expectations
- `design-log/architecture.md` — power tree, data paths, block interfaces, risks
- `design-log/decisions.md` — one entry per architectural decision with alternatives rejected
- `design-log/open-questions.md` — the queue
- Optional `blocks/<id>.yaml` — per-block intent

Hand off to `@component-select` (IC mode) with the locked IC list.

## Will not

- Assign LCSC numbers or run `fetch-part` → `@component-select`
- Run pin-by-pin datasheet walkthroughs → `@datasheet-research`
- Select passive part numbers → `@component-select` passive mode
- Edit schematics or run ERC → the user draws; `@schematic-review` checks

## Session summary format

```markdown
## Design consultation — <board>

**Locked**
- Rail V3V3 3.3 V from buck-boost, 500 mA peak
- Block `regulation` → TPS63802 (alternative: TPS63020, rejected on area)

**Open (blocking)**
- q-load-current — V3V3 peak load unknown; regulator sizing waits on it

**Written**
- design.yaml (rails, blocks), design-log/architecture.md, decisions.md

**Next**
- `@component-select` IC mode for: TPS63802, BQ25895
```
