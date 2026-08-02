# kicad-cursor

Chat-driven KiCad design pipeline for Cursor agents. Combines MCP servers, project skills, and a shared component library to scaffold schematics and PCBs from conversation.

## Prerequisites

- KiCad 10 with IPC API enabled (`Preferences → Plugins → Enable IPC API Server`)
- Python 3.11+ with [uv](https://github.com/astral-sh/uv) (for MCP servers)
- WSL Ubuntu with `fetchPart` / `easyeda2kicad` (for LCSC part imports)
- Cursor with MCP support

## Quick start

1. Open this folder in Cursor.
2. Enable MCP servers from `.cursor/mcp.json` (see [docs/setup.md](docs/setup.md)).
3. Start KiCad and open a project under `projects/`.
4. Chat with the agent using skills like `@kicad-project`, `@component-select`, `@schematic-design`.

## Repository layout

```
kicad-cursor/
  .cursor/
    mcp.json              # KiCad MCP server config
    skills/               # Agent skills for design workflows
  docs/
    setup.md              # Full setup instructions
  projects/
    template/             # Copy this to start a new board
  scripts/
    fix-symbol-lib.py     # Repair easyeda2kicad malformed .kicad_sym
  design.yaml             # Root example (see projects/template/)
```

## Shared library

All designs use the personal **global** KiCad library:

- Symbols: `C:/Users/Elli Furedy/projects/global-kicad-lib/global.kicad_sym`
- Footprints: `C:/Users/Elli Furedy/projects/global-kicad-lib/global.pretty`
- 3D models: `C:/Users/Elli Furedy/projects/global-kicad-lib/global.3dshapes`

Import new LCSC parts from WSL:

```bash
fetchPart C80200
```

## Workflow

```text
Chat intent → Agent reads design.yaml + datasheets
           → component-select picks parts from global lib (or fetchPart)
           → schematic MCP creates/updates .kicad_sch
           → PCB MCP places footprints, pours, tracks (live IPC)
           → design-verify runs ERC/DRC via kicad-cli
```

## License

MIT
