---
name: kicad-project
description: KiCad project conventions for cyon1c hardware designs — global library paths, WSL fetchPart workflow, KiCad 10 config, and kicad-cursor repo layout. Use when starting or editing KiCad projects, configuring libraries, or importing LCSC parts.
---

# KiCad Project Conventions

## Repository

- Workspace root: `kicad-cursor/` in `~/projects`
- New boards: copy `projects/template/` → `projects/<board-name>/`
- Always read `design.yaml`, `constraints.md`, and `bom-targets.yaml` in the active project folder first

## Global library (Windows paths)

| Resource | Path |
|----------|------|
| Symbols | `C:/Users/Elli Furedy/projects/global-kicad-lib/global.kicad_sym` |
| Footprints | `C:/Users/Elli Furedy/projects/global-kicad-lib/global.pretty` |
| 3D models | `C:/Users/Elli Furedy/projects/global-kicad-lib/global.3dshapes` |

Library nickname in schematics/PCBs: **`global`** (e.g. `global:BQ25895RTWR`).

## Import missing parts (WSL)

```bash
wsl bash -lc "fetchPart C80200"
wsl bash -lc "python3 '/mnt/c/Users/Elli Furedy/projects/kicad-cursor/scripts/fix-symbol-lib.py'"
```

Functions defined in `/home/cyonic/fetchPart.sh`: `fetchPart`, `fetchFootprint`, `fetchSymbol`, `fetch3d`.

## KiCad 10

- CLI: `"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"`
- Config: `%APPDATA%/kicad/10.0/`
- IPC API must be enabled for live MCP editing

## Agent workflow

1. Read project `design.yaml` for intent and rails
2. Check `bom-targets.yaml` before selecting new parts
3. Prefer existing `global` symbols over creating new ones
4. After schematic edits → ERC; after PCB edits → DRC
5. Never mark complete without `@design-verify`

## MCP servers

Configured in `.cursor/mcp.json`: `kicad-pcb`, `kicad-schematic`. KiCad must be running.

See [docs/setup.md](../../docs/setup.md) for full setup.
