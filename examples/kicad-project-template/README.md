# KiCad project template

Copy these files into your KiCad project directory (the folder containing your `.kicad_pro` file).

```powershell
Copy-Item -Recurse examples/kicad-project-template/* C:/path/to/my-board/
```

```bash
cp -R examples/kicad-project-template/. ~/projects/my-board/
```

Then:

1. Create or open the KiCad project in that folder (`File → New Project`).
2. Point `kicad-cursor.yaml` at the folder (see repo root `kicad-cursor.yaml.example`).
3. Edit `design.yaml`, `constraints.md`, and `bom-targets.yaml` for your board — the examples are placeholders, not defaults to keep.
4. Add datasheet PDFs under `datasheets/` and run `extract-datasheet` (see [datasheets/README.md](datasheets/README.md)).
5. Start a session with `@design-consultant`.

## What each file is for

| Path | Owner | Purpose |
|------|-------|---------|
| `design.yaml` | `@design-consultant` | Intent: rails, blocks, constraints, open questions |
| `constraints.md` | `@design-consultant` | Schematic/PCB rules, value-field policy, review gate |
| `bom-targets.yaml` | `@component-select` | Symbol → LCSC registry with selection `status` |
| `datasheets/` | user + `extract-datasheet` | Source PDFs and extracted markdown/tables |
| `research/<MPN>/` | `@datasheet-research` | Per-IC overview, pins, required passives |
| `design-log/` | all roles | Decisions, open questions, IC and passive selections, reviews |
| `design-context/` | `dump-design-context` | **Generated** as-built netlist context — do not hand-edit |
| `blocks/<id>.yaml` | `@design-consultant` | Optional per-block intent: ICs, passives by role, nets |

`research/_template/` and `design-log/` ship pre-filled with example rows so the shape is obvious. Replace or delete them once your board has real content.

## Roles and gates

The workflow is IC-before-passives, and **the user draws the schematic** — agents never edit `.kicad_sch`. See [docs/workflow.md](../../docs/workflow.md) for the short guide and [docs/workflow-plan.md](../../docs/workflow-plan.md) for the authoritative plan.

This repo does **not** store KiCad board files. Your schematic, PCB, and project metadata live in your project directory.
