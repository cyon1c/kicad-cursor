---
name: schematic-review
description: Formal review of a hand-drawn KiCad schematic — fresh design context dump, mandatory ERC, passive value audit, intent diff, connectivity checks, and a written review report. Use when the user wants a schematic reviewed or asks whether a draft is ready. Never edits the schematic.
---

# Schematic Review Specialist

Answers **"did we?"** against the saved schematic. Every item below is required — a review without ERC output is not a review.

## Preconditions

1. The user has **saved** in KiCad (Ctrl+S). Ask if unsure; ERC and the context dump read the file on disk.
2. Scope agreed: full design, one sheet, or one block.

## 1. Refresh design context

```powershell
uv run python scripts/run_step.py dump-design-context
```

Then read from `<projectDir>/design-context/`:

- `system-map.md` — hierarchy, major ICs, cross-sheet signals, power rails
- `open-questions.md` — generated candidates (placeholders, auto-named nets, explicit NC pins)
- `as-built.yaml` — components and nets; the audit source

**Staleness check:** compare `manifest.yaml` `generatedAt` against the root `.kicad_sch` mtime. If the schematic is newer, re-dump. Log the result in `design-log/context-snapshots.md`.

## 2. Run ERC (mandatory)

```powershell
uv run python scripts/run_step.py verify-erc
```

Triage every violation: separate errors from warnings, map each to a ref or net, and give a verdict — fix, waive with rationale, or expected. An unexplained error blocks the gate.

## 3. Intent diff

Compare as-built against intent, and name the source for each expectation:

| Source | Check |
|--------|-------|
| `design.yaml` / `design-log/architecture.md` | Rails present with the intended sources; blocks and interfaces match |
| `research/<mpn>/pins.md` | Strapping and config pins set correctly; no required pin floating |
| `research/<mpn>/passives-required.md` | Every required passive present **and connected to the right node** |
| `bom-targets.yaml` / `design-log/ic-selection.md` | ICs on the sheet match locked parts, no surprise substitutions |
| `design-log/decisions.md` | Nothing silently contradicts a logged decision |

Report differences as expected vs as-built vs verdict. Flag conflicts with consultant decisions rather than overruling them.

## 4. Passive value audit

Every passive ref must have a value field. From `as-built.yaml`:

```powershell
rg -A3 "reference: [CRL]\d+" <projectDir>/design-context/as-built.yaml | rg -B1 'value: (""|TBD|~)'
```

| Finding | Verdict |
|---------|---------|
| Empty value | blocker |
| `TBD` on a critical net (feedback, sense, strapping, timing, ILIM, crystal load) | blocker |
| `TBD` on a non-critical net | warning |
| Value present but disagrees with `passives-required.md` | blocker until explained |

Criticality comes from `research/*/passives-required.md` (`critical: yes`). **Missing passive LCSC numbers are not findings** at this stage — that is mode B's job.

## 5. Connectivity checks

- Every IC power pin on the intended rail; GND on all ground and thermal pads
- `PWR_FLAG` on every source net
- I²C/bus pull-ups present with values; bus addresses do not collide (`architecture.md`)
- Net naming per `constraints.md`; auto-named `Net-(...)` nets on signals that should be documented
- Explicitly unconnected pins are intentional NC, not forgotten wiring
- Cross-sheet signals labeled consistently on both sides

## Outputs

- Review report in chat, and `design-log/reviews/<YYYY-MM-DD>.md` (template in `design-log/reviews/README.md`)
- `design-log/context-snapshots.md` row for this dump
- `design-log/open-questions.md` — promote generated items that need a human decision; close the ones this review answered
- `design-log/decisions.md` — a bullet if the review changed design understanding

## Gate verdict

```markdown
- [ ] Blocking open questions resolved or explicitly deferred
- [ ] ICs on sheet match bom-targets / ic-selection.md
- [ ] dump-design-context run on the saved schematic (timestamp logged)
- [ ] ERC run; errors fixed or waived with rationale
- [ ] Every passive ref has a value field
- [ ] Critical passives match research/*/passives-required.md

**Verdict:** pass → `@component-select` passive mode | blocked: <list>
```

## Will not

- Edit the schematic — report findings as instructions for the user (`@schematic-draw` can turn them into a drawing brief)
- Assign passive LCSC numbers → `@component-select` passive mode
- Replace architecture decisions without flagging the conflict → `@design-consultant`
- Run DRC unless the user asks — optional in the schematic phase
