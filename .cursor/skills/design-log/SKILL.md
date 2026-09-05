---
name: design-log
description: Append and synthesize project continuity notes in design-log/ — decisions, open questions, IC and passive selections, reviews, context snapshots. Use at the end of any session that changed design intent, parts, or schematic understanding, or when catching up on prior sessions.
---

# Design Log

Continuity across sessions and roles. Not a separate persona — every role writes here before ending a session.

## Minimum append rule

**Any session that changes intent, parts, or schematic understanding adds at least one bullet to `decisions.md` or updates `open-questions.md`.** A session that ends with nothing written is a session whose reasoning is lost.

## File ownership

Location: `<projectDir>/design-log/`

| File | Owner | Content |
|------|-------|---------|
| `decisions.md` | all roles | ADR-style: date, role, decision, rationale, alternatives rejected, affects |
| `open-questions.md` | `@design-consultant` queues; any role closes | Single human-facing question list |
| `ic-selection.md` | `@component-select` mode A | Locked ICs with LCSC and rationale |
| `passive-bom.md` | `@component-select` mode B | Value → LCSC, after review only |
| `architecture.md` | `@design-consultant` | Power tree, data paths, block interfaces, risks |
| `reviews/<date>.md` | `@schematic-review` | ERC summary and findings |
| `context-snapshots.md` | `@schematic-review` | Dump timestamp vs schematic mtime |

`design-context/` is **generated** by `dump-design-context` — never hand-edit it. Promote items from `design-context/open-questions.md` into `design-log/open-questions.md` when they need a human decision.

## Append conventions

- **Newest first** in `decisions.md`; never rewrite history, add a superseding entry that links the old one
- One decision per entry; keep it to a few lines and link `research/` or `datasheets/extracted/` instead of restating specs
- Always name the **role** that made the decision — it tells the next session which gate the change belongs to
- Reversing a prior decision requires an explicit "supersedes <date> — <reason>" line
- Question states: `open` → `deferred` (with reason) or `closed` (with a link to the `decisions.md` entry)
- Dates are ISO (`YYYY-MM-DD`)

### Decision entry

```markdown
### 2026-03-14 — Charger switched to BQ25619 for power path

- **Role:** component (IC)
- **Decision:** BQ25619LRTWR replaces BQ25895RTWR.
- **Rationale:** Needs system rail while charging; §8.2 power path.
- **Alternatives rejected:** BQ25895 — no power path in the stocked variant.
- **Affects:** block `input`; rail `VSYS`; supersedes 2026-02-01 charger choice.
```

## Catch-up mode

Starting a session on an unfamiliar board — read in this order and stop when you have what you need:

1. `design-log/decisions.md` (newest 10 entries) — what is settled
2. `design-log/open-questions.md` — what is not
3. `design.yaml` + `design-log/architecture.md` — the shape of the design
4. `design-log/reviews/` (latest) — where the schematic stood
5. `design-log/context-snapshots.md` — whether that review is still current

Then state the phase the project is in and which skill should run next.

## Synthesis

When `decisions.md` grows past readability, add a **Current state** section at the top summarizing what holds now, keeping the entries below untouched as history. Do not delete entries.

## Will not

- Make design decisions — record them
- Edit schematics, run ERC, or assign part numbers
- Hand-edit `design-context/`
