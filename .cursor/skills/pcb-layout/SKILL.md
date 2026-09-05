---
name: pcb-layout
description: PCB layout guidance — placement order, routing priorities, pours. Deferred until the schematic workflow is stable; use only when the user explicitly starts layout work on a board whose schematic has passed review.
---

# PCB Layout (deferred phase)

> **Status: deferred.** The layout workflow is not defined yet — see `docs/workflow-plan.md` §7 Deferred. Do not start layout until the schematic has passed `@schematic-review` and passives are `passive-locked`. The guidance below is a starting point, not a role definition.

## Prerequisites

- KiCad PCB Editor open with target board loaded
- IPC API server enabled
- Schematic updated and netlist imported (or board synced from schematic)
- MCP server `konnect` connected; load PCB toolsets as needed (`@konnect`)

## Placement order

1. Board outline and mounting holes
2. Connectors (fixed position / edge constraints)
3. Power path (charger, regulators, inductors)
4. MCU / main IC
5. Decoupling caps adjacent to IC power pins
6. Remaining passives

## Routing priorities

1. Power rails (wide traces, short paths)
2. High-speed or sensitive nets (I2C, USB D+/D-, crystal)
3. GPIO and slow signals

## Design rules (defaults from constraints.md)

- 2-layer unless design.yaml specifies more
- Min track 0.15 mm, min clearance 0.15 mm
- Power tracks: size for expected current (ask user if unknown)

## Copper pours

- GND pour on bottom layer (default)
- Split or route carefully around high-current switch nodes

## Autorouting

KiCad IPC does not expose a native autorouter API. Options:

1. Manual routing via MCP track creation
2. Export to FreeRouting (external tool) — ask user before using
3. Route critical nets only; leave rest for user review

## After layout changes

Always run `@design-verify` (DRC) only when the user asks.

## Live feedback

Changes via IPC appear immediately in the PCB editor. Ask the user to confirm visually for critical placement decisions.
