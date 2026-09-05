# Passive BOM

Owner: `@component-select` **passive mode** (Mode B). **Do not fill this before schematic review signs off.**

Entry gate (all must hold):

- [ ] Schematic reviewed; topology approved
- [ ] ERC run; errors fixed or waived with rationale
- [ ] Every passive ref has a value field
- [ ] Critical values match `research/*/passives-required.md`

## Value → LCSC mapping

One row per distinct value/package combination, not per ref.

| Value | Package | Voltage / rating | LCSC | Refs | Notes |
|-------|---------|------------------|------|------|-------|
| 100nF | 0402 | 16 V X7R | Cxxxxxx | C1, C4, C7 | IC decoupling |
| 10µF | 0805 | 25 V X5R | Cxxxxxx | C2 | VBUS bulk |
| 4.7k | 0402 | 1% | Cxxxxxx | R1, R2 | I²C pull-ups |

Mirror into `bom-targets.yaml` with `status: passive-locked`.

## Package and rating policy

- Default passive package: 0402 unless current, voltage, or hand-assembly says otherwise
- Capacitor voltage rating ≥ 2× rail; X7R/X5R for decoupling, no Y5V
- Resistor tolerance: 1% default; tighter only where research calls for it (sense, feedback, timing)

## Intentional generics

Parts left as library placeholders on purpose — record why, so review does not re-flag them.

| Ref | Value | Reason |
|-----|-------|--------|
| — | — | — |
