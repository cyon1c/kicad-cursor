# KiCad + Claude Code setup

Works on Windows, macOS, and Linux. Where commands differ, both forms are shown — PowerShell first, then macOS/Linux shell.

## Platform paths

| | Windows | macOS | Linux |
|---|---------|-------|-------|
| KiCad config | `%APPDATA%/kicad/10.0/` | `~/Library/Preferences/kicad/10.0/` | `~/.config/kicad/10.0/` |
| User project templates | `%USERPROFILE%/Documents/KiCad/10.0/template/` | `~/Documents/KiCad/10.0/template/` | `~/Documents/kicad/10.0/template/` |
| `kicad-cli` | `C:/Program Files/KiCad/10.0/bin/kicad-cli.exe` | `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli` | `/usr/bin/kicad-cli` |
| JLC parts DB | `%APPDATA%/konnect/jlcpcb.db` | `~/Library/Application Support/konnect/jlcpcb.db` | `~/.local/share/konnect/jlcpcb.db` |

`kicad-cli` is auto-detected from `PATH` first, then the platform default above. Override with `kicadCli` in `kicad-cursor.yaml` or the `KICAD_CLI` env var.

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

```bash
cp kicad-cursor.yaml.example kicad-cursor.yaml
```

Set `activeProject` and `projects` in `kicad-cursor.yaml`, plus `symbolLibrary.path` for your shared library. See [usage.md](usage.md).

## 3. MCP server (Konnect)

The plugin ships `.mcp.json` with one server:

| Server | Purpose |
|--------|---------|
| `konnect` | Schematic + PCB + exports + JLCPCB (on-demand toolsets) |

**Install Konnect binary** (once) — picks the right release asset for your OS and CPU:

```bash
uv run python scripts/install_konnect.py     # --version v0.11.0 --force to override
```

Installs to `bin/konnect` (`bin/konnect.exe` on Windows), which the plugin's `.mcp.json` launches through `scripts/run_konnect.py`. The launcher needs `uv` on your PATH and no Python packages, so it starts before `uv sync`.

Prebuilt binaries exist for Windows x86-64, macOS (Intel and Apple Silicon), and Linux x86-64. On other targets such as Linux arm64, build from source or install the KiCad plugin via **Plugin and Content Manager** → [latest release](https://github.com/mixelpixx/Konnect/releases) → `konnect-pcm-<version>-<os>.zip`, then point `.mcp.json` at that binary.

**Requirements:**

- KiCad 10 running with IPC enabled (for PCB tools)
- PCB Editor open with target board for live PCB edits
- Schematic tools work on `.kicad_sch` files without KiCad open

Check with `/mcp` in Claude Code: only `konnect` (from the `kicad` plugin) should be listed for KiCad.

Use `/kicad:konnect` skill for toolset loading rules. Use `/kicad:kicad-step` for cataloged low-token steps (outline, fetch-part, verify).

## 4. JLCPCB parts database (for `/kicad:component-select`)

Konnect's `get_jlcpcb_part` / `search_jlcpcb_parts` tools need a local parts database, which Konnect downloads and builds itself (requires v0.3.0 or later — the installer ships v0.11.0):

1. In chat, ask the agent to call `download_jlcpcb_database` (integration toolset).
2. Verify with `get_jlcpcb_database_stats`.

The cache path per OS is in the [Platform paths](#platform-paths) table. This is a one-time setup (re-run occasionally to refresh stock data). No scripts in this repo are required.

## 5. LCSC part imports

Parts are imported via `easyeda2kicad` in the repo venv:

```powershell
kicad-step fetch-part --lcsc-id C80200
uv run python scripts/fetch_part.py C80200 --symbol    # symbol only
uv run python scripts/fetch_part.py C80200 --footprint # footprint only
```

Output goes to the library path in `kicad-cursor.yaml` (`symbolLibrary.path/global.*`).

`fetch_part.py` runs `fix-symbol-lib.py` automatically after full/symbol imports. easyeda2kicad 1.x sometimes appends symbols outside the library block, which makes KiCad ignore them.

## 6. KiCad library tables

Configure KiCad to find your shared library. Example for a library nicknamed `global`. These files live in the KiCad config directory from [Platform paths](#platform-paths).

**Symbols** (`sym-lib-table`):

```
(lib (name "global") (uri "${GLOBAL}/global.kicad_sym") ...)
```

**Footprints** (`fp-lib-table`):

```
(lib (name "global") (uri "${GLOBAL}/global.pretty") ...)
```

**Environment** (`kicad_common.json`) — set `GLOBAL` to your library root:

```json
"GLOBAL": "/Users/you/projects/global-kicad-lib"
```

On Windows use forward slashes or escaped backslashes (`C:/path/to/global-kicad-lib`).

## 7. Starting a new board project

**Option A — KiCad user template (repeat use):** register `examples/kicad-project-template/` as a user template via `KICAD_USER_TEMPLATE_DIR`, add a blank KiCad project in that folder, then use **File → New Project → User Templates**. Full steps: [examples/kicad-project-template/README.md](../examples/kicad-project-template/README.md#option-a--kicad-user-template-recommended-for-repeat-use).

**Option B — Manual copy:**

1. Create a folder for your board (outside this repo).
2. Copy metadata from `examples/kicad-project-template/` (skip `meta/`).
3. Create the KiCad project in that folder (`File → New Project`).
4. Add the folder as a project target: `kicad-projects add my-board C:/path/to/folder` (or set `projects` in `kicad-cursor.yaml`).

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

Manual verification, bypassing the step runner:

```bash
kicad-cli sch erc /path/to/my-board/my-board.kicad_sch
kicad-cli pcb drc /path/to/my-board/my-board.kicad_pcb
```

If `kicad-cli` is not on your PATH, use the full path from [Platform paths](#platform-paths).

## 9. Agent skills

Invoke **one** explicitly per session — see [workflow.md](workflow.md) for the phase order:

- `/kicad:design-consultant` — requirements, power tree, blocks, IC intent
- `/kicad:component-select` — LCSC and library: IC mode, then passive mode after review
- `/kicad:datasheet-research` — per-IC pins, strapping, required passives
- `/kicad:schematic-draw` — drawing briefs for you (agents never edit `.kicad_sch`)
- `/kicad:schematic-review` — context dump + ERC + value audit + intent diff
- `/kicad:design-log` — decisions, open questions, session catch-up
- `/kicad:kicad-project` — config, libraries, project layout
- `/kicad:kicad-step` — run one cataloged script
- `/kicad:konnect` — JLC lookup and read-only context via MCP
- `/kicad:design-verify` — ad-hoc ERC/DRC (opt-in only)
- `/kicad:pcb-layout` — deferred until the layout phase is defined

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| No KiCad project configured | Create `kicad-cursor.yaml` from example |
| MCP can't connect | KiCad not running or IPC disabled (PCB tools) |
| Konnect not found | Run `uv run python scripts/install_konnect.py` or install the PCM plugin |
| MCP server fails to start | `uv` must be on your PATH — the plugin's `.mcp.json` launches Konnect through it |
| `kicad-cli not found` | Add KiCad to your PATH or set `kicadCli` in `kicad-cursor.yaml` |
| Old kicad-mcp still loading | `claude mcp list`, then `claude mcp remove <name>` for anything but `konnect` |
| Symbols missing after fetchPart | Run `fix-symbol-lib`, restart KiCad |
| Footprints not found | Check fp-lib-table name is `global`, path is `global.pretty` |
| ERC or context dump looks stale | Save the schematic in KiCad (Ctrl+S) — both read the file on disk |
| `permission denied` on `scripts/bin/*` | `chmod +x scripts/bin/fetch-part scripts/bin/extract-datasheet` |
