# Architecture

Owner: `@design-consultant`. The narrative behind `design.yaml` — power tree, data paths, block interfaces.

## Power tree

```text
USB-C VBUS 5V ──> charger ──> VSYS ──> buck-boost ──> V3V3 ──> MCU, sensors
                     │
                   VBAT (1S Li-ion 3.0–4.2V)
```

For each rail: source, nominal voltage, worst-case current, sequencing requirement.

| Rail | Source | Voltage | Max current | Sequencing |
|------|--------|---------|-------------|------------|
| VBUS | USB-C | 5.0 V | 1.5 A | — |
| VSYS | charger power path | 3.0–5.0 V | — | after VBUS or VBAT |
| V3V3 | buck-boost | 3.3 V | TBD | after VSYS |

## Data paths

| Bus | Master | Devices | Notes |
|-----|--------|---------|-------|
| I²C | MCU | charger, fuel gauge | pull-ups on V3V3, addresses must not collide |

## Block interfaces

For each block in `design.yaml`: inputs, outputs, and the signals crossing to other blocks. This is the contract the schematic review diffs against.

| Block | In | Out | Crossing signals |
|-------|----|-----|------------------|
| input | USB-C | VBUS | VBUS, GND |
| regulation | VBUS, VBAT | V3V3 | V3V3, GND, PG |
| mcu | V3V3 | — | I2C_SDA, I2C_SCL |

## Risks

- <risk> → mitigation, and which open question tracks it
