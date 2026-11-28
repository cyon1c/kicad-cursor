---
name: design-verify
description: Ad-hoc KiCad ERC and DRC runs when the user explicitly asks to verify, validate, or check the design. Never runs automatically. For a full schematic review with intent diff and value audit, use schematic-review instead.
---

# Design Verification (ad-hoc, opt-in)

## Critical rule

**Do not run ERC or DRC after edits or any other step unless the user explicitly requests verification** (or invokes `/kicad:design-verify`).

Wrong: draw outline → run DRC automatically.
Right: draw outline → remind user to Ctrl+S → stop.

## This skill vs `/kicad:schematic-review`

| | `/kicad:design-verify` | `/kicad:schematic-review` |
|---|---|---|
| Trigger | User says "run ERC/DRC" | User wants a design review |
| Scope | Raw check output only | Fresh context dump + **ERC** + value audit + intent diff |
| ERC | Only if asked | **Always required** |
| Output | Pass/fail + violations | Review report, `design-log/reviews/<date>.md` |

If the user asks for a *review*, use `/kicad:schematic-review` — it runs ERC as part of its checklist. Use this skill only for a quick standalone check.

## Commands (via step runner)

Uses `activeProject` from `kicad-cursor.yaml`:

```bash
kicad-step verify-erc
kicad-step verify-drc
kicad-step verify-all
```

Both checks read the **saved** files on disk. Remind the user to save in KiCad first.

DRC is optional in the schematic phase — the board is expected to be incomplete.

## Symbol library (only after fetch-part)

```bash
kicad-step fix-symbol-lib
```

## Report format

```markdown
## Verification: <project>

### ERC — PASS | FAIL
### DRC — PASS | FAIL (or SKIPPED — schematic phase)
```

List violations only for checks that were requested and failed. Group by error vs warning and map each to a ref or net.
