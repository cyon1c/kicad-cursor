# Context snapshots

Owner: `@schematic-review`. Proves each review ran against a **fresh** dump of the **saved** schematic.

Append a row every time `dump-design-context` runs. If the schematic mtime is newer than the dump, the review is stale — re-dump.

| Dump (UTC) | Schematic mtime | Fresh? | Components | Nets | Open questions | Review |
|------------|-----------------|--------|-----------|------|----------------|--------|
| 2026-01-01T12:00:00Z | 2026-01-01 11:58 | yes | 42 | 37 | 9 | `reviews/2026-01-01.md` |

Dump timestamp comes from `design-context/manifest.yaml` (`generatedAt`); counts come from the step output.
