# <MPN> — overview

- **Role in this design:** <block id> — one line
- **Package:** <package> (<pin count>)
- **Datasheet:** `datasheets/<file>.pdf` → `datasheets/extracted/<stem>/`
- **Locked in:** `design-log/ic-selection.md` YYYY-MM-DD

## What it does

One paragraph: the job of this IC in plain language.

## Key specs

Cite the extracted table for each row.

| Spec | Value | Source |
|------|-------|--------|
| Supply range | | `tables/<n>.yaml` |
| Absolute max | | |
| Quiescent / operating current | | |
| Switching frequency | | |
| Control interface | | |

## Where it sits

```text
<upstream rail/block> ──> <MPN> ──> <downstream rail/block>
```

- **Rails in:** from `design.yaml`
- **Rails out:**
- **Control signals:**

## Reference design

Which datasheet figure is the applicable typical application circuit, and how this design differs from it.

- **Figure:** <e.g. Figure 8-1>
- **Deviations:** <what we do differently and why>

## Open items

- [ ] <unknown> — needs user decision or datasheet section not yet extracted
