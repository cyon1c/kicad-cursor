# KiCad + Cursor setup

## 1. KiCad IPC API

1. Open KiCad 10.
2. Go to **Preferences → Plugins**.
3. Enable **IPC API Server**.
4. Keep KiCad running while using MCP tools.

For PCB work, open **PCB Editor** with your board loaded.
For schematic work, open **Schematic Editor** with your schematic loaded.

## 2. Configure kicad-cursor

Copy and edit the local config:

```powershell
Copy-Item kicad-cursor.yaml.example kicad-cursor.yaml
```

Set `projectDir` to your KiCad project folder and `symbolLibrary.path` to your shared library. See [usage.md](usage.md).

## 3. MCP server (Konnect)

This repo ships `.cursor/mcp.json` with one server:

| Server | Purpose |
|--------|---------|
| `konnect` | Schematic + PCB + exports + JLCPCB (on-demand toolsets) |

**Install Konnect binary** (once):

```powershell
.\scripts\install_konnect.ps1
```

Or install the KiCad plugin via **Plugin and Content Manager** → [v0.2.2 release](https://github.com/mixelpixx/Konnect/releases) → `konnect-pcm-v0.2.2-windows.zip`, then update `.cursor/mcp.json` if the binary path differs.

**Requirements:**

- KiCad 10 running with IPC enabled (for PCB tools)
- PCB Editor open with target board for live PCB edits
- Schematic tools work on `.kicad_sch` files without KiCad open

**Cursor:** disable old `kicad-pcb` / `kicad-schematic` servers if still cached, then reload MCP. Only `konnect` should be enabled.

Use `@konnect` skill for toolset loading rules. Use `@kicad-step` for cataloged low-token steps (outline, fetch-part, verify).

## 4. JLCPCB parts database (for `@component-select`)

Konnect's `get_jlcpcb_part` / `search_jlcpcb_parts` tools need a local parts database. **Konnect v0.3.0+** downloads and builds this automatically:

1. Use Konnect v0.3.0 or later (re-run `scripts/install_konnect.ps1` or install the latest PCM release).
2. In chat, ask the agent to call `download_jlcpcb_database` (integration toolset).
3. Verify with `get_jlcpcb_database_stats`.

Default cache locations:

| OS | Path |
|----|------|
| Windows | `%APPDATA%/konnect/jlcpcb.db` |
| macOS | `~/Library/Application Support/konnect/jlcpcb.db` |
| Linux | `~/.local/share/konnect/jlcpcb.db` |

This is a one-time setup (re-run occasionally to refresh stock data). No scripts in this repo are required.

## 5. LCSC part imports

Parts are imported via `easyeda2kicad` in the repo venv:

```powershell
uv run python scripts/run_step.py fetch-part --lcsc-id C80200
uv run python scripts/fetch_part.py C80200 --symbol    # symbol only
uv run python scripts/fetch_part.py C80200 --footprint # footprint only
```

Output goes to the library path in `kicad-cursor.yaml` (`symbolLibrary.path/global.*`).

`fetch_part.py` runs `fix-symbol-lib.py` automatically after full/symbol imports. easyeda2kicad 1.x sometimes appends symbols outside the library block, which makes KiCad ignore them.

## 6. KiCad library tables

Configure KiCad to find your shared library. Example for a library nicknamed `global`:

**Symbols** (`%APPDATA%/kicad/10.0/sym-lib-table`):

```
(lib (name "global") (uri "C:/path/to/global-kicad-lib/global.kicad_sym") ...)
```

**Footprints** (`%APPDATA%/kicad/10.0/fp-lib-table`):

```
(lib (name "global") (uri "${GLOBAL}/global.pretty") ...)
```

**Environment** (`kicad_common.json`):

```json
"GLOBAL": "C:\\path\\to\\global-kicad-lib\\"
```

## 7. Starting a new board project

1. Create a folder for your board (outside this repo).
2. Copy metadata from `examples/kicad-project-template/`.
3. Create the KiCad project in that folder (`File → New Project`).
4. Set `projectDir` in `kicad-cursor.yaml` to that folder.

## 8. Python environment and tests

```powershell
uv sync
```

Run basic tests:

```powershell
# IPC connection — KiCad running; open PCB Editor for full pass
uv run python scripts/test_ipc.py

# ERC/DRC via kicad-cli — no GUI required
uv run python scripts/test_kicad_cli.py
```

Expected IPC output when **PCB Editor** is open with your board:

```text
OK: Connected to KiCad 10.0.x
OK: Active PCB has N footprint(s)
```

If you see `PCB editor not ready`, open your `.kicad_pcb` in PCB Editor (not just the project manager).

Manual verification:

```powershell
$project = (Get-Content kicad-cursor.yaml | Select-String 'projectDir:').ToString().Split(':',2)[1].Trim()
& "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" sch erc "$project/*.kicad_sch"
& "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb drc "$project/*.kicad_pcb"
```

## 9. Agent skills

Invoke **one** explicitly per session — see [workflow.md](workflow.md) for the phase order:

- `@design-consultant` — requirements, power tree, blocks, IC intent
- `@component-select` — LCSC and library: IC mode, then passive mode after review
- `@datasheet-research` — per-IC pins, strapping, required passives
- `@schematic-draw` — drawing briefs for you (agents never edit `.kicad_sch`)
- `@schematic-review` — context dump + ERC + value audit + intent diff
- `@design-log` — decisions, open questions, session catch-up
- `@kicad-project` — config, libraries, project layout
- `@kicad-step` — run one cataloged script
- `@konnect` — JLC lookup and read-only context via MCP
- `@design-verify` — ad-hoc ERC/DRC (opt-in only)
- `@pcb-layout` — deferred until the layout phase is defined

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| No KiCad project configured | Create `kicad-cursor.yaml` from example |
| MCP can't connect | KiCad not running or IPC disabled (PCB tools) |
| Konnect not found | Run `scripts/install_konnect.ps1` or install PCM plugin |
| Old kicad-mcp still loading | Remove disabled servers in Cursor MCP settings, reload |
| Symbols missing after fetchPart | Run `fix-symbol-lib`, restart KiCad |
| Footprints not found | Check fp-lib-table name is `global`, path is `global.pretty` |
| ERC or context dump looks stale | Save the schematic in KiCad (Ctrl+S) — both read the file on disk |
