# IC selection

Owner: `@component-select` **IC mode** (Mode A), after `@design-consultant` locks architecture.

Only ICs and electromechanical parts belong here. Passives go in `passive-bom.md` **after** schematic review.

## Locked ICs

| Block | Ref intent | MPN | LCSC | Symbol | Footprint class | Status |
|-------|-----------|-----|------|--------|-----------------|--------|
| charger | U1 | BQ25619LRTWR | C2913166 | `global:BQ25619LRTWR` | WQFN-24 | ic-locked |

Mirror each row into `bom-targets.yaml` with `status: ic-locked`.

## Rationale

```markdown
### <MPN> — <role>
- **Why:** requirement it satisfies (from design.yaml / constraints.md)
- **Key specs:** the two or three numbers that decided it
- **Stock:** JLC stock and package at time of selection
- **Library:** in library | imported via fetch-part on YYYY-MM-DD
- **Datasheet:** datasheets/<file>.pdf → extracted/<stem>/
- **Alternatives rejected:** MPN — reason
```

---

### BQ25619LRTWR — 1-cell charger with power path

- **Why:** USB-C input, 1S Li-ion, needs system rail while charging.
- **Key specs:** 1.5 A charge, integrated power path, I²C control.
- **Stock:** example only — verify before committing.
- **Library:** imported via `fetch-part` on 2026-01-01.
- **Datasheet:** `datasheets/bq25619.pdf` → `datasheets/extracted/bq25619/`
- **Alternatives rejected:** BQ25896 — no power path variant in stock.
