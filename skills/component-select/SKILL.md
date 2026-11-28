---
name: component-select
description: Part sourcing and library management in two modes — IC intake (LCSC + fetch-part for ICs after design consultation) and passive finalize (LCSC for passives only after schematic review). Use when assigning LCSC numbers, importing symbols, or updating bom-targets.yaml.
---

# Component Selection

Two modes with a **hard gate** between them. State which mode you are in before doing anything.

| Mode | Entry condition | Scope |
|------|-----------------|-------|
| **A — IC intake** | `/kicad:design-consultant` locked IC intent per block | ICs and electromechanical parts only |
| **B — Passive finalize** | `/kicad:schematic-review` signed off | Passives only |

**Never assign passive LCSC numbers in mode A.** While the user is drawing, passives carry a value field and nothing else.

## Shared: library lookup

Use the path from `kicad-cursor.yaml` (`symbolLibrary.path`):

```bash
rg 'BQ25895|C80200' <symbolLibrary.path>/global.kicad_sym
```

Symbol names are usually the manufacturer MPN, not the LCSC ID.

## Shared: JLC lookup

Konnect, read-only (`/kicad:konnect`): `load_toolset("jlcpcb_parts")`, then `search_jlcpcb_parts` / `get_jlcpcb_part`. One-time `download_jlcpcb_database`.

Check: stock, package, basic vs extended, price at build quantity.

## Shared: import

```bash
kicad-step fetch-part --lcsc-id C80200
```

Symbol repair runs automatically (`fix-symbol-lib`). Set the schematic footprint field to `global:<footprint_name>`.

---

## Mode A — IC intake

**Entry:** `design.yaml` `blocks[].ics` has MPN intent, or the user names an IC.

1. Read `bom-targets.yaml` — reuse a listed part if it fits.
2. Search the symbol library for the MPN.
3. Verify against the datasheet before committing — supply range and absolute max, package availability, control interface, thermal pad:
   - Run `extract-datasheet` if `datasheets/extracted/<stem>/` is missing or stale
   - Read `tables/*.yaml` for specs; `pages/*.md` for prose
   - Do not guess a critical spec — cite the section or ask
4. JLC check: stock and package match the design's assembly constraints.
5. `fetch-part` if not in the library.
6. Write `bom-targets.yaml` entry with `status: ic-locked` (LCSC required, `null` only when sourcing is deliberately off-JLC — say so in `notes`).
7. Append to `design-log/ic-selection.md`: decision, key specs, stock, alternatives rejected.

**Will not:** assign passive LCSC numbers; walk pins (→ `/kicad:datasheet-research`).

**Hand off:** `/kicad:datasheet-research` per locked IC.

### Report per IC

```markdown
- **MPN**: BQ25895RTWR
- **LCSC**: C80200 (stock 4.2k, extended)
- **Symbol**: global:BQ25895RTWR
- **Footprint**: global:QFN-24_L4.0-W4.0-P0.50-TL-EP2.7
- **Status**: in library | imported via fetch-part
- **Block**: input
- **Rationale**: one line, with the spec that decided it
```

---

## Mode B — Passive finalize

**Entry gate — verify all of these before touching a single LCSC number:**

- [ ] `design-log/reviews/<date>.md` exists with a pass verdict
- [ ] ERC errors fixed or waived with written rationale
- [ ] Every passive on the schematic has a value field
- [ ] Critical values match `research/*/passives-required.md`

If any box fails, stop and hand back to `/kicad:schematic-review`.

1. Build the distinct value/package list from `design-context/as-built.yaml` (group refs by value — one LCSC per value/package, not per ref).
2. For each group, apply the rating rules in `constraints.md`: capacitor voltage ≥ 2× rail, X7R/X5R for decoupling (no Y5V), 1% resistors by default, tighter where research demands.
3. JLC search per group — prefer basic parts, check stock against build quantity.
4. `fetch-part` only if the package/value symbol is missing from the library.
5. Update `bom-targets.yaml` passive entries to `status: passive-locked` with LCSC.
6. Write `design-log/passive-bom.md`: value → LCSC table with refs, package, rating notes, and any intentional generics.

**Will not:** re-architect blocks, redo pin walkthroughs, or change values — a value change means going back to `/kicad:datasheet-research` or `/kicad:design-consultant`.

### Report

```markdown
## Passive finalize — <board>

| Value | Package | Rating | LCSC | Refs | Basic? |
|-------|---------|--------|------|------|--------|

**Imported:** N new symbols via fetch-part
**Intentional generics:** <ref> — reason
**Written:** bom-targets.yaml (passive-locked), design-log/passive-bom.md
```
