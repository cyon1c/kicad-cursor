---
name: kicad-step
description: Execute a single cataloged KiCad operation via run_step.py. Use when the user asks to extract a datasheet, dump design context, fetch a part, draw an outline, test IPC, or run a specific named action. Do not explore kipy or MCP for steps listed in steps.yaml.
---

# KiCad Step Runner

## Rule: one step = one command

Never grep kipy, read API docs, or run ERC/DRC unless the step id is `verify-erc`, `verify-drc`, or `verify-all`, or the user explicitly asks to verify.

```powershell
uv run python scripts/run_step.py <step-id> [--project-dir C:/path/to/my-board] [--lcsc-id C80200]
```

Project path comes from `kicad-cursor.yaml` unless `--project-dir` is passed.

List steps: `uv run python scripts/run_step.py --list`

## Step ids

| Id | When | Role |
|----|------|------|
| `extract-datasheet` | PDF → `<project>/datasheets/extracted/<stem>/` — requires `--pdf` | `@datasheet-research` |
| `fetch-part` | Import LCSC part — requires `--lcsc-id` | `@component-select` |
| `fix-symbol-lib` | After `fetch-part` | `@component-select` |
| `dump-design-context` | Export as-built schematic context to `<project>/design-context/` | `@schematic-review` |
| `verify-erc` | Schematic ERC — required in a formal review | `@schematic-review`, `@design-verify` |
| `verify-drc` | PCB DRC (board must be saved first) — optional in schematic phase | `@design-verify` |
| `verify-all` | User explicitly wants both | `@design-verify` |
| `draw-board-outline` | Board outline / Edge.Cuts rectangle — PCB phase | — |
| `test-ipc` | Confirm KiCad IPC + PCB editor connection — PCB phase | — |

Full catalog: [steps.yaml](../../../steps.yaml)

## Retired

`run-block` is retired (`retiredSteps:` in steps.yaml). Agents no longer generate schematic content — the user draws. Use `@schematic-draw` for a drawing brief and `@schematic-review` to check the result.

## On failure

If an IPC step fails, tell the user to open the PCB Editor and enable IPC. Do not chain `test-ipc` + `draw-board-outline` + `verify-drc` unless asked.

## Adding new steps

Add an entry to `steps.yaml` and implement the script. Do not inline kipy in chat.
