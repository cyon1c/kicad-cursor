# kicad-cursor

Chat-driven KiCad design utilities for Cursor agents. This repo provides MCP integration, agent skills, and scripts that operate on **your existing KiCad project** — it does not contain board designs.

**You draw the schematic.** The agents handle requirements, power architecture, part sourcing, datasheet research, and review with ERC — they never edit your `.kicad_sch`. See [docs/workflow.md](docs/workflow.md).

Runs on Windows, macOS, and Linux.

## Prerequisites

- KiCad 10 with IPC API enabled (`Preferences → Plugins → Enable IPC API Server`)
- Python 3.11+ with [uv](https://github.com/astral-sh/uv)
- [Konnect](https://github.com/mixelpixx/Konnect) MCP server (see [docs/setup.md](docs/setup.md))
- Cursor with MCP support
- A KiCad project on disk (`.kicad_pro` + schematic/PCB files)

## Quick start

1. Clone this repo and open it in Cursor.
2. Copy `kicad-cursor.yaml.example` → `kicad-cursor.yaml` and set paths (forward slashes and `~` work everywhere):

   ```yaml
   activeProject: my-board
   projects:
     my-board: ~/projects/my-board
   symbolLibrary:
     nickname: global
     path: ~/projects/global-kicad-lib
   ```

3. Install dependencies: `uv sync`
4. Install Konnect: `python scripts/install_konnect.py`
5. Enable the `konnect` MCP server from `.cursor/mcp.json`.
6. Copy `examples/kicad-project-template/*` into your project folder and open the project in KiCad.
7. Start a session: `@design-consultant`.

## Workflow at a glance

| # | Phase | Skill |
|---|-------|-------|
| 1 | Requirements, power tree, blocks, IC intent | `@design-consultant` |
| 2 | IC intake — LCSC + `fetch-part` | `@component-select` (IC mode) |
| 3 | Per-IC pins and required passives | `@datasheet-research` |
| 4 | **You draw the schematic in KiCad** | `@schematic-draw` (briefs only) |
| 5 | Review — context dump + ERC + value audit | `@schematic-review` |
| 6 | Passive LCSC finalize | `@component-select` (passive mode) |

ICs get part numbers up front; passives carry only a value until review passes. PCB layout is a deferred phase.

See [docs/workflow.md](docs/workflow.md) for the guide, [docs/workflow-plan.md](docs/workflow-plan.md) for the authoritative plan, and [docs/usage.md](docs/usage.md) for tooling.

## Repository layout

```
kicad-cursor/
  .cursor/
    mcp.json              # Konnect MCP server config
    rules/                # Agent rules (external project model)
    skills/               # Agent skills for design workflows
  docs/
    setup.md              # KiCad, Konnect, library setup
    usage.md              # Pointing tools at your project
    workflow.md           # Six-phase schematic workflow guide
    workflow-plan.md      # Authoritative roles, gates, implementation plan
    steps.md              # Token-efficient step catalog
  examples/
    kicad-project-template/  # Copy into your KiCad project folder
  scripts/                # CLI utilities (fetch-part, verify, extract, etc.)
  steps.yaml              # Catalog of atomic agent operations
  kicad-cursor.yaml.example
```

## Common commands

Identical in PowerShell, zsh, and bash:

```bash
# Import an LCSC part into your symbol library
uv run python scripts/run_step.py fetch-part --lcsc-id C80200

# Export schematic context for agent review
uv run python scripts/run_step.py dump-design-context

# Run ERC/DRC (only when you ask)
uv run python scripts/run_step.py verify-all

# Override project for one command
uv run python scripts/run_step.py dump-design-context --project my-board
uv run python scripts/run_step.py dump-design-context --project-dir ~/projects/my-board

# List and switch named project targets
uv run python scripts/manage_projects.py list
uv run python scripts/manage_projects.py use my-board
```

Project resolution order: `--project-dir` → `--project` → `KICAD_PROJECT_DIR` → `KICAD_PROJECT` → `activeProject` in `kicad-cursor.yaml` → legacy `projectDir`.

## License

[GNU Affero General Public License v3.0](LICENSE) or later (`AGPL-3.0-or-later`).

Copyright (C) 2026 Alleycat Asset Acquisitions. See [NOTICE](NOTICE) for the copyright and warranty statement.

Hardware designs you create with these tools are separate works — license your boards under whatever terms you choose (e.g. CERN-OHL, proprietary). This repository is software only.
