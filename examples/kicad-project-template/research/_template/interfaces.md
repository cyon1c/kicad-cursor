# <MPN> — interfaces

Optional. Write this only when the IC has a bus, timing, or sequencing requirement that affects how the schematic is drawn.

## Bus

| Property | Value | Source |
|----------|-------|--------|
| Interface | I²C / SPI / UART | |
| Address (and strap options) | | |
| Max clock | | |
| Logic levels (VIH / VIL) | | |
| Internal pull-ups? | | |

Address collisions with other devices on the same bus — check against `design-log/architecture.md`.

## Power sequencing

Order in which rails and enables must come up, and what enforces it in the schematic.

```text
1. <rail> stable
2. <enable> released after <delay>
```

## Timing

| Parameter | Min | Typ | Max | Source |
|-----------|-----|-----|-----|--------|

## Interrupts and status pins

| Pin | Direction | Idle state | Needs pull-up? | Consumer |
|-----|-----------|-----------|----------------|----------|

## Firmware notes

Anything the MCU must do that constrains the schematic (bootstrap pins, GPIO capabilities, wake sources).
