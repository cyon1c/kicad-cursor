# <MPN> — required passives

Values and nominals only. **LCSC = TBD** until `@component-select` passive mode runs after review.

This file is what `@schematic-review` diffs the as-built schematic against, so mark criticality honestly.

| Role | Pin / node | Value | Tolerance | Rating | Critical? | Source |
|------|-----------|-------|-----------|--------|-----------|--------|
| VIN bulk | VIN–GND | 10µF | 20% | ≥ 2× rail | no | `tables/<n>.yaml` |
| VIN decoupling | VIN–GND | 100nF | 10% | 16 V | no | typical app circuit |
| Feedback divider top | FB | 100k | 1% | — | **yes** | eq. <n> |
| Current sense | SNS | 0.01Ω | 1% | ≥ <power> | **yes** | eq. <n> |
| Boost inductor | SW | 2.2µH | 20% | Isat ≥ <n> A | **yes** | §<n> |

**Critical = yes** for anything that sets a voltage, current limit, timing, or strapping state. Review blocks on a missing or `TBD` critical value; non-critical `TBD` is only a warning.

## Calculated values

Show the equation and inputs so a reviewer can re-derive the number.

```text
R_ILIM = <equation from §n>
       = <inputs>
       = <result> → nearest 1% standard value <value>
```

## Subcircuits

Groups of passives that only make sense together (snubber, NTC network, crystal load caps).

### <subcircuit name>

| Role | Value | Note |
|------|-------|------|

## Not required

Datasheet-optional components deliberately omitted, and why — prevents review flagging them as missing.

| Component | Why omitted |
|-----------|-------------|
