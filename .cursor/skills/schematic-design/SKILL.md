---
name: schematic-design
description: Create and modify KiCad schematics using MCP tools or file-based editing — components, nets, hierarchical sheets, power symbols, and decoupling patterns. Use when building or changing schematics, wiring nets, or adding circuit blocks.
---

# Schematic Design

## Before editing

1. Read `design.yaml` blocks and rails
2. Read `constraints.md` net naming and decoupling rules
3. Confirm required parts via `@component-select`

## Approach (pick one)

**Live IPC** (KiCad + Eeschema open, MCP `kicad-schematic`):
- Best for iterative tweaks with visible UI feedback

**File-based** (fallback):
- Edit `.kicad_sch` via schematic MCP or direct generation
- User reloads schematic in Eeschema (File → Revert or reopen)

## Structure rules

- One functional block per hierarchical sheet when design.yaml lists multiple blocks
- Net labels on all cross-sheet connections; use hierarchical labels for sheet ports
- Power symbols: `+3V3`, `+5V`, `GND` — consistent with design.yaml rail names
- Reference designators: `U` ICs, `R` resistors, `C` capacitors, `L` inductors, `J` connectors

## Decoupling template (per IC)

For each IC power pin:

1. 100 nF (`C0402`) close to pin
2. Bulk 4.7 µF or 10 µF on the rail near the IC cluster

## Common patterns

| Block | Minimum parts |
|-------|---------------|
| LDO input | 1 µF + 100 nF on IN |
| LDO output | 10 µF + 100 nF on OUT |
| Buck converter | Input cap, output cap, inductor per datasheet |
| I2C bus | 4.7 kΩ pull-ups to V3V3 (if not internal) |
| Reset/EN | Pull-up + optional button to GND |

## After changes

Run ERC via `@design-verify` before proceeding to PCB work.

## MCP reminder

Schematic IPC is newer than PCB IPC. If tools fail, switch to file-based schematic MCP or manual Eeschema reload.
