# KiCad + Cursor setup

## 1. KiCad IPC API

1. Open KiCad 10.
2. Go to **Preferences → Plugins**.
3. Enable **IPC API Server**.
4. Keep KiCad running while using MCP tools.

For PCB work, open **PCB Editor** with your board loaded.
For schematic work, open **Schematic Editor** with your schematic loaded.

## 2. MCP servers (Cursor)

This repo ships `.cursor/mcp.json` with two servers:

| Server | Purpose |
|--------|---------|
| `kicad-pcb` | Live footprint placement, tracks, zones, DRC |
| `kicad-schematic` | Live schematic editing (KiCad 10+, early support) |

**Requirements:**

- [uv](https://github.com/astral-sh/uv) on PATH
- KiCad running with IPC enabled

On first use, Cursor will run `uvx kicad-mcp`, which downloads dependencies automatically.

### Optional: file-based schematic MCP

If live schematic IPC is unstable, add a file-based server using [KiCAD-Schematic-Manipulation](https://github.com/richard-luc/KiCAD-Schematic-Manipulation):

```json
"kicad-sch-files": {
  "command": "python",
  "args": ["-m", "mcp_kicad_sch_api"]
}
```

Install first: `pip install kicad-sch-api` (plus that repo's MCP package).

## 3. WSL fetchPart (LCSC imports)

Parts are imported from Ubuntu WSL:

```bash
fetchPart C80200          # full symbol + footprint + 3D
fetchFootprint C80200     # footprint only
fetchSymbol C80200        # symbol only
```

Script location: `/home/cyonic/fetchPart.sh` (sourced from `~/.profile`).

Output library:

```
C:/Users/Elli Furedy/projects/global-kicad-lib/
  global.kicad_sym
  global.pretty/
  global.3dshapes/
```

After every `fetchPart`, run:

```bash
python scripts/fix-symbol-lib.py
```

easyeda2kicad 1.x sometimes appends symbols outside the library block, which makes KiCad ignore them.

## 4. KiCad library tables

Ensure these are configured (already set on this machine):

**Symbols** (`%APPDATA%/kicad/10.0/sym-lib-table`):

```
(lib (name "global") (uri "C:/Users/Elli Furedy/projects/global-kicad-lib/global.kicad_sym") ...)
```

**Footprints** (`%APPDATA%/kicad/10.0/fp-lib-table`):

```
(lib (name "global") (uri "${GLOBAL}/global.pretty") ...)
```

**Environment** (`kicad_common.json`):

```json
"GLOBAL": "C:\\Users\\Elli Furedy\\projects\\global-kicad-lib\\"
```

## 5. Starting a new board project

```bash
cp -r projects/template projects/my-board
cd projects/my-board
# Edit design.yaml, constraints.md, bom-targets.yaml
# Add datasheets to datasheets/
# Create KiCad project in KiCad: File → New Project
```

## 6. Verification commands

```powershell
& "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" sch erc my-board.kicad_sch
& "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb drc my-board.kicad_pcb
```

## 7. Agent skills

Invoke explicitly in chat:

- `@kicad-project` — paths, libraries, project layout
- `@component-select` — pick parts, fetchPart, datasheets
- `@schematic-design` — schematic structure and wiring rules
- `@pcb-layout` — placement and routing via IPC
- `@design-verify` — ERC/DRC gate before finishing

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| MCP can't connect | KiCad not running or IPC disabled |
| Symbols missing after fetchPart | Run `fix-symbol-lib.py`, restart KiCad |
| Footprints not found | Check fp-lib-table name is `global`, path is `global.pretty` |
| Schematic MCP no-op | Use file-based MCP or edit .kicad_sch + reload in Eeschema |
