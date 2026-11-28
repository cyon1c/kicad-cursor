---
name: konnect
description: Use Konnect MCP read-only for KiCad design context and JLCPCB part lookup. Use when searching JLC parts, checking stock, or reading project/schematic context. Never for schematic placement or wiring.
---

# Konnect MCP (read-only in the schematic phase)

Single MCP server (`konnect`). In the schematic phase Konnect is a **lookup and context** tool, not an authoring tool.

## Hard boundary

**The user draws schematics.** Never call schematic-modifying tools:

| Allowed | Forbidden |
|---------|-----------|
| `download_jlcpcb_database` | `add_schematic_component` |
| `get_jlcpcb_part`, `search_jlcpcb_parts` | `sch_wiring` toolset (`add_wire`, labels, power symbols) |
| `get_jlcpcb_database_stats` | Any tool that writes `.kicad_sch` |
| Read-only project/schematic context tools | PCB placement and routing (deferred to layout phase) |

If a task seems to need schematic edits, stop and hand the drawing back to the user — describe what to place and how to wire it instead.

## Context economy

- Baseline `tools/list` is the **starter kit**: `project` + `config` toolsets + meta-tools
- `list_toolboxes` — the source of truth for which toolsets this build has
- `load_toolset(name)` before use; `unload_toolset(name)` when switching tasks
- In the schematic phase you should normally load only `jlcpcb_parts`

## Prefer steps over Konnect

| Task | Use |
|------|-----|
| Schematic connectivity / as-built context | `/kicad:kicad-step` → `dump-design-context` (kicad-cli netlist — reliable, no image processing) |
| ERC / DRC | `/kicad:kicad-step` → `verify-erc` / `verify-drc` |
| Import LCSC part into the library | `/kicad:kicad-step` → `fetch-part` |
| Datasheet extraction | `/kicad:kicad-step` → `extract-datasheet` |
| JLC search, stock, price | Konnect `jlcpcb_parts` toolset |

`dump-design-context` — not Konnect — is the primary schematic context path.

## JLC lookup flow

1. `load_toolset("jlcpcb_parts")`
2. One-time per machine: `download_jlcpcb_database` (needs v0.3.0+; `install_konnect.py` ships v0.11.0)
3. `search_jlcpcb_parts` / `get_jlcpcb_part` — check stock, package, price
4. Import the chosen part with `fetch-part`, then record it in `bom-targets.yaml`

Part identity and BOM rules live in `/kicad:component-select` (IC mode vs passive mode).

## PCB tools — deferred

PCB placement and routing toolsets are out of scope until the layout phase is defined (see `docs/workflow-plan.md` §7 Deferred). They require KiCad 10 running with the IPC API enabled and the PCB Editor open.

## Installation

The plugin's `.mcp.json` launches `scripts/run_konnect.py` through `uv`, which works on Windows, macOS, and Linux. The binary lives at `bin/konnect` (`bin/konnect.exe` on Windows):

```bash
uv run --project <repo> python <repo>/scripts/install_konnect.py
```

If the server fails to start, check that `uv` is on PATH and the binary exists — see the troubleshooting table in `docs/setup.md`.

## Meta-tools (always available)

- `list_toolboxes`, `load_toolset`, `unload_toolset`, `get_active_toolsets`
- `get_recent_calls`, `server_stats` — debug failed tool calls
