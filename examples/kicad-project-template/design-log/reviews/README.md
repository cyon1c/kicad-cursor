# Reviews

One file per formal schematic review: `<YYYY-MM-DD>.md` (add `-2` for a second pass the same day).

Written by `@schematic-review`. Every report includes ERC output — a review without ERC is incomplete.

## Report template

```markdown
# Schematic review — YYYY-MM-DD

- **Schematic:** <root .kicad_sch>, saved <mtime>
- **Context dump:** design-context/manifest.yaml generatedAt <timestamp>
- **Scope:** full design | block <id> | sheet <name>

## ERC

- Errors: N | Warnings: N
| Severity | Rule | Ref / net | Verdict |
|----------|------|-----------|---------|
| error | pin_not_connected | U1.PG | fix — needs pull-up |

## Intent diff

| Expected (source) | As-built | Verdict |
|-------------------|----------|---------|
| V3V3 from buck-boost (architecture.md) | matches | ok |

## Passive value audit

| Ref | Value | Critical? | Verdict |
|-----|-------|-----------|---------|
| R7 | TBD | yes — feedback divider | blocker |

## Connectivity

- Power pins / GND: …
- PWR_FLAG on sources: …
- Pull-ups: …
- Net naming vs constraints.md: …

## Gate

- [ ] Topology approved
- [ ] ERC clean or waived with rationale
- [ ] All passives have values
- [ ] Critical passives match research

**Verdict:** pass → passive finalize | blocked (list blockers)
```
