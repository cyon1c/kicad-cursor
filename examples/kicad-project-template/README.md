# KiCad project template

Agent metadata for a new board. This repo does **not** ship `.kicad_pro` / `.kicad_sch` / `.kicad_pcb` files — you create those in KiCad (or via a user template below).

## Option A — KiCad user template (recommended for repeat use)

Register this folder as a KiCad user template so **File → New Project** copies both KiCad files and agent metadata in one step.

### One-time setup

1. Confirm KiCad's user template folder: **Preferences → Configure Paths** → `KICAD_USER_TEMPLATE_DIR`. On Windows, KiCad usually creates `~/Documents/KiCad/10.0/template/` on first run — use that if it already exists (no need for a separate folder).
2. Copy this entire directory into that template folder and rename it to your template name (e.g. `kicad-cursor-board`). Keep the `meta/` folder — KiCad needs it for the template picker and does not copy it into new projects.

   ```powershell
   Copy-Item -Recurse examples/kicad-project-template "$env:USERPROFILE/Documents/KiCad/10.0/template/kicad-cursor-board"
   ```

3. In KiCad, create a blank project **in that template folder** with the **same base name** as the folder (e.g. `kicad-cursor-board.kicad_pro`). Preconfigure anything you want every board to inherit (sheet size, title block, board outline, design rules).
4. Optional: add a 64×64 `meta/icon.png` for the template picker.

### Starting a new board

1. **File → New Project** → **User Templates** → **kicad-cursor board** → choose location and project name.
2. Add the folder as a project target: `kicad-projects add my-board C:/path/to/folder` (see `kicad-cursor.yaml.example`).
3. Edit `design.yaml`, `constraints.md`, and `bom-targets.yaml` — the shipped examples are placeholders, not defaults to keep.
4. Add datasheet PDFs under `datasheets/` and run `extract-datasheet` (see [datasheets/README.md](datasheets/README.md)).
5. Start a session with `/kicad:design-consultant`.

KiCad renames files that contain the template folder name to match the new project name (e.g. `kicad-cursor-board.kicad_pro` → `my-gadget.kicad_pro`). Other paths (`design.yaml`, `datasheets/`, etc.) keep their names. Dotfiles (e.g. `.gitkeep`) are not copied.

Remove `*-backups`, `.history`, and `.git` from the template folder before relying on it so those are not copied into new projects.

## Option B — Manual copy

Copy metadata into an existing or new KiCad project directory (the folder containing your `.kicad_pro` file). Skip `meta/` — it is only for KiCad's template picker.

```powershell
Get-ChildItem examples/kicad-project-template -Exclude meta | Copy-Item -Destination C:/path/to/my-board/ -Recurse
```

```bash
rsync -a --exclude meta examples/kicad-project-template/ ~/projects/my-board/
```

Then:

1. Create or open the KiCad project in that folder (`File → New Project`).
2. Point `kicad-cursor.yaml` at the folder (see repo root `kicad-cursor.yaml.example`).
3. Edit `design.yaml`, `constraints.md`, and `bom-targets.yaml` for your board — the examples are placeholders, not defaults to keep.
4. Add datasheet PDFs under `datasheets/` and run `extract-datasheet` (see [datasheets/README.md](datasheets/README.md)).
5. Start a session with `/kicad:design-consultant`.

## What each file is for

| Path | Owner | Purpose |
|------|-------|---------|
| `design.yaml` | `/kicad:design-consultant` | Intent: rails, blocks, constraints, open questions |
| `constraints.md` | `/kicad:design-consultant` | Schematic/PCB rules, value-field policy, review gate |
| `bom-targets.yaml` | `/kicad:component-select` | Symbol → LCSC registry with selection `status` |
| `datasheets/` | user + `extract-datasheet` | Source PDFs and extracted markdown/tables |
| `research/<MPN>/` | `/kicad:datasheet-research` | Per-IC overview, pins, required passives |
| `design-log/` | all roles | Decisions, open questions, IC and passive selections, reviews |
| `design-context/` | `dump-design-context` | **Generated** as-built netlist context — do not hand-edit |
| `blocks/<id>.yaml` | `/kicad:design-consultant` | Optional per-block intent: ICs, passives by role, nets |
| `meta/` | user | KiCad template picker only (`info.html`, optional `icon.png`) — not copied to new projects |

`research/_template/` and `design-log/` ship pre-filled with example rows so the shape is obvious. Replace or delete them once your board has real content.

## Roles and gates

The workflow is IC-before-passives, and **the user draws the schematic** — agents never edit `.kicad_sch`. See [docs/workflow.md](../../docs/workflow.md) for the short guide and [docs/workflow-plan.md](../../docs/workflow-plan.md) for the authoritative plan.

This repo does **not** store KiCad board files. Your schematic, PCB, and project metadata live in your project directory.
