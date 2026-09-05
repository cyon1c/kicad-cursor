# Design decisions

ADR-style log. **Every session that changes intent, parts, or schematic understanding appends at least one entry here** (or updates `open-questions.md`).

Newest first. Keep entries short — link to `research/` or `datasheets/extracted/` instead of restating specs.

## Template

```markdown
### YYYY-MM-DD — <decision in one line>

- **Role:** consultant | component (IC) | research | review | component (passive)
- **Decision:** what was chosen
- **Rationale:** why, with a datasheet section or spec reference
- **Alternatives rejected:** option — reason
- **Affects:** blocks, rails, or refs
```

---

### 2026-01-01 — Example: V3V3 supplied by buck-boost, not LDO

- **Role:** consultant
- **Decision:** Single buck-boost from VBAT to V3V3 for the whole board.
- **Rationale:** Battery spans 3.0–4.2 V; an LDO would drop out at the low end.
- **Alternatives rejected:** LDO — dropout; two-stage boost+LDO — cost and area.
- **Affects:** blocks `regulation`, `mcu`; rail `V3V3`.
