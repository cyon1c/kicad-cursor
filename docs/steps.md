# Token-efficient steps

## Problem

An agent can burn thousands of tokens per action by:

- Grepping `kipy` to rediscover the API each time
- Running IPC tests, DRC, and file reads "just to be safe"
- Reading multiple skills and project files before a single command

## Solution: step catalog + thin agent

```text
User intent  →  step id  →  run_step.py  →  purpose-built script  →  KiCad
                (1 lookup)   (1 shell)         (no agent reasoning)
```

| Layer | Who holds the knowledge |
|-------|-------------------------|
| `steps.yaml` | Step id, command, prerequisites |
| `scripts/*.py` | kipy/API details |
| Agent | Pick step id, run one command, report output |

## Agent rules

1. **One user action → one step id → one shell command**
2. **Never explore kipy/MCP** for cataloged steps
3. **Never run verify-*** unless the user asks
4. **Don't read design.yaml** before atomic steps (scripts read it if needed)
5. **On IPC failure**, suggest prerequisites — don't chain test-ipc + verify-drc

## Example: draw board outline

Before (high token):

- grep kipy for Edge_Cuts, BoardSegment, create_items
- run test_ipc.py
- write inline Python
- run DRC unprompted

After (low token):

```powershell
uv run python scripts/run_step.py draw-board-outline
```

(Project path comes from `kicad-cursor.yaml`.)

## Adding a step

1. Implement `scripts/my_action.py`
2. Add entry to `steps.yaml`
3. Optionally extend `@kicad-step` table — no API exploration in skills

## Verification is separate

| Step | When |
|------|------|
| `draw-board-outline` | User wants outline |
| `verify-drc` | User says "run DRC" / `@design-verify` |
| `verify-all` | User says "verify the design" |
