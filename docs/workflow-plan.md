# Schematic design workflow plan

This document is the **authoritative plan** for how kicad-cursor supports hand-drawn schematic design. It defines roles, gates, project layout, tools, and implementation order. Skills and templates should be built to match this plan — not the other way around.

**Status:** Implemented (2026-09-05) — Phases 0–4 of §7 are complete; skills, templates, and docs match this document. Remaining items are in §7 Deferred.  
**Scope:** Schematic phase only. PCB layout workflow is deferred.

See also: [workflow.md](workflow.md) (user-facing guide derived from this plan), [usage.md](usage.md) (tooling), [setup.md](setup.md) (install), [steps.md](steps.md) (atomic commands).

---

## 1. Principles (non-negotiable)

| Principle | Meaning |
|-----------|---------|
| **User draws schematics** | All edits to `.kicad_sch` are made by the human in KiCad. Agents do not place, wire, or modify schematic sheets. |
| **Konnect is read-only for schematics** | Konnect provides accurate **design context** (connectivity, parts on sheet) and **JLCPCB part lookup** — not schematic authoring. No `add_schematic_component`, routing, or placement via MCP for schematic work. |
| **External project model** | Board files and metadata live in the user's KiCad project directory (`projectDir` in `kicad-cursor.yaml`), not in this repo. |
| **ICs before passives (selection)** | After design consultation, only **ICs** (and electromechanical parts) get LCSC numbers and `fetch-part` imports. **Passive LCSC assignment** happens after schematic build and review. |
| **Values before passive LCSC** | At schematic review, every passive must have a **value field** (e.g. `100nF`, `10k`, `0.01Ω`). LCSC part numbers for passives are filled in the later passive pass. |
| **Review includes ERC** | Schematic review is not complete without running ERC on the saved schematic and triaging violations. |
| **Datasheets are extracted, not re-read** | Agents use `datasheets/extracted/<stem>/` (especially `tables/*.yaml`), not raw PDFs or screenshots, for pin-level research. |
| **One active role per session** | Invoke one specialist skill at a time to avoid role bleed (consultant doing LCSC search, reviewer picking parts, etc.). |

---

## 2. Specialist roles

Five conceptual specialists. **Documentation** is a shared artifact layer, not a separate chat persona.

Step 4 of §3 is the human's, so it has no specialist — `@schematic-draw` only turns consultant intent and research into a drawing brief for the user, and never touches `.kicad_sch`.

### 2.1 PCB Design Consultant

**Purpose:** Requirements, system architecture, and block-level decisions before detailed IC and pin work.

**When:** Project start, major architecture changes, or when `openQuestions` in `design.yaml` block progress.

**Inputs:**
- User goals and constraints
- Existing `design.yaml`, `constraints.md` (if any)
- High-level competitive or reference designs (user-provided)

**Outputs:**
- Updated `design.yaml`: `rails`, `blocks`, `constraints`, `openQuestions`
- Updated `constraints.md`: schematic/PCB rules, naming, verification expectations
- Optional `design-log/architecture.md`: power tree, data paths, block interfaces
- **IC shortlist or locked set per block** (MPN-level intent, not necessarily LCSC yet)

**Will not:**
- Run pin-by-pin datasheet walkthroughs (→ Research)
- Assign LCSC numbers (→ Component)
- Edit schematics or run ERC (→ Review)
- Select passive part numbers

**Prior art:** Power-tree and architecture discussions in [Targeted electrical engineering concepts](c8465072-d3ce-41cb-8888-bfc3ed2d9370); open-question driven gaps in [Extract skill on SSD1315 PDF](c5348864-71c8-4512-8836-5638828976cd).

**Skill:** `@design-consultant` (implemented).

---

### 2.2 Schematic Research Assistant

**Purpose:** Deep understanding of how a **selected IC** works — features, pins, passives roles, reference design — so the user can draw the schematic correctly.

**When:** After an IC is chosen (or shortlisted to one candidate) for a block.

**Inputs:**
- PDF in `datasheets/<mpn>.pdf` (user adds)
- `extract-datasheet` output under `datasheets/extracted/<stem>/`
- Consultant context: `design.yaml` rails/blocks, `research` index

**Outputs** (under `research/<mpn>/`):
- `overview.md` — what the chip does, key features, where it sits in the system
- `pins.md` — pin-by-pin: function, type, strapping, external components **by role** (not LCSC)
- `passives-required.md` — required/nominal passives per pin or subcircuit (values/nominals OK; LCSC = TBD)
- Optional `interfaces.md` — I²C/SPI/USB behavior, timing, sequencing
- Links back to `datasheets/extracted/<stem>/tables/*.yaml` for specs

**Walkthrough format** (from prior sessions):
1. Chip overview (job of the IC in one paragraph)
2. Pin-by-pin narrative with passive influence on each pin
3. Grouped pins where appropriate (e.g. all LED sink outputs, all power pins)
4. Application schematic decoded vs pin table (see BQ25619 “Figure 8-1” style explanations)
5. “Path from IC to IC” — how rails and signals flow to the next block

**Will not:**
- Assign LCSC or run `fetch-part` (→ Component)
- Edit schematics
- Run ERC
- Lock passive BOM entries

**Prior art:** BQ25619 pin and application-schematic threads in [Targeted electrical engineering concepts](c8465072-d3ce-41cb-8888-bfc3ed2d9370); IS31FL3236A grouped pin walkthrough in [LEDs and drivers discussion](cecacd34-7cc6-4cd8-9cd1-d12475b7fc4c).

**Skill:** `@datasheet-research` (implemented). Output template: `examples/kicad-project-template/research/_template/`.

**Tools:**
```powershell
uv run python scripts/run_step.py extract-datasheet --pdf datasheets/<file>.pdf
```

---

### 2.3 Component Research Assistant

**Purpose:** Sourcing, library management, and part identity. Two **distinct modes** with a hard gate between them.

#### Mode A — IC intake (after Consultant)

**When:** IC decisions are made per block.

**Outputs:**
- LCSC ID, MPN, symbol (`global:<name>`), footprint class
- `fetch-part` for missing library entries
- `bom-targets.yaml` entries for ICs only (`status: ic-locked`)
- `design-log/ic-selection.md` append: decision + rationale

**Will not:** Assign passive LCSC numbers.

#### Mode B — Passive finalize (after Review sign-off)

**When:** Schematic draft reviewed; all passives have value fields; topology approved.

**Outputs:**
- LCSC for each passive (or approved generic placeholders where intentional)
- Updated `bom-targets.yaml` passive section (`status: passive-locked`)
- `design-log/passive-bom.md`: value → LCSC mapping, package/voltage notes

**Will not:** Re-architect blocks or redo full pin walkthroughs.

**Prior art:** JLC search and `fetch-part` in [Low current RGB LEDs](d43950d5-c367-48e9-9f8f-5ba59542108b); passive policy in [PCB design next steps](cb361dd1-4829-431d-9bba-c27f41de54b0).

**Skill:** `@component-select` (refactored into explicit mode A / mode B).

**Tools:**
```powershell
uv run python scripts/run_step.py fetch-part --lcsc-id C80200
uv run python scripts/run_step.py fix-symbol-lib
```
Konnect (v0.3.0+): `download_jlcpcb_database`, `get_jlcpcb_part`, `search_jlcpcb_parts` — **read/lookup only**.

---

### 2.4 Schematic Review Specialist

**Purpose:** Verify the **as-built** hand-drawn schematic against design intent, research artifacts, and electrical rules.

**When:** User has a draft schematic worth reviewing (per block or full sheet).

**Inputs:**
- Saved `.kicad_sch` (user must save in KiCad before review)
- `design.yaml`, `constraints.md`, `research/<mpn>/`
- `design-log/` decisions

**Activities (all required for a complete review):**

1. **Refresh design context**
   ```powershell
   uv run python scripts/run_step.py dump-design-context
   ```
   Read `design-context/system-map.md`, `open-questions.md`, `as-built.yaml`.

2. **Run ERC**
   ```powershell
   uv run python scripts/run_step.py verify-erc
   ```
   Triage violations; distinguish errors vs warnings; map to refs/nets.

3. **Intent diff** — Compare as-built to:
   - Consultant: rails, blocks, interfaces
   - Research: strapping, required passives **present and connected**
   - IC `bom-targets` vs symbols on sheet

4. **Passive value audit** — Every passive ref has a **value field**. Flag `TBD`, empty, or generic placeholders on **critical** nets (feedback, sense, strapping, timing).

5. **Connectivity checks** — Power pins, GND, PWR_FLAG on sources, I²C pull-ups (present as values even if LCSC TBD), net naming per `constraints.md`.

**Outputs:**
- Review report (chat + optional `design-log/reviews/<date>.md`)
- Updated `design-context/open-questions.md` items promoted or closed
- ERC/DRC status summary (ERC required; DRC optional in schematic phase)

**Will not:**
- Edit the schematic
- Assign passive LCSC (→ Component mode B)
- Replace Consultant architecture decisions without flagging conflict

**Prior art:** `dump-design-context` origin in [PCB design next steps](cb361dd1-4829-431d-9bba-c27f41de54b0); connectivity review patterns in [Schematic errors resolution](6c34d766-232f-434f-8a38-8fad8f1292f8).

**Skill:** `@schematic-review` (implemented; supersedes ad-hoc `@design-verify` for review passes). Report template: `examples/kicad-project-template/design-log/reviews/README.md`.

**Note on `@design-verify`:** Keep as opt-in for ad-hoc ERC/DRC outside formal review. **Formal schematic review always includes ERC.**

---

### 2.5 Documentation (shared layer)

**Purpose:** Continuity across sessions and roles — decisions, open questions, cross-links.

**Not a separate agent.** Every role appends to shared files before ending a session.

**Location:** `<projectDir>/design-log/`

| File | Owner | Content |
|------|-------|---------|
| `decisions.md` | All roles | ADR-style: date, decision, rationale, alternatives rejected |
| `open-questions.md` | Consultant (queue); others close | Single open-question list |
| `ic-selection.md` | Component mode A | Locked ICs with LCSC + rationale |
| `passive-bom.md` | Component mode B | Value → LCSC after review |
| `architecture.md` | Consultant | Power/data block diagram, rail strategy |
| `reviews/<date>.md` | Review | ERC summary + findings |
| `context-snapshots.md` | Review | Timestamp of last `dump-design-context` vs schematic save |

**Minimum append rule:** Any session that changes intent, parts, or schematic understanding adds at least one bullet to `decisions.md` or updates `open-questions.md`.

**Prior art:** `design-decisions.md` updates in [Low current RGB LEDs](d43950d5-c367-48e9-9f8f-5ba59542108b).

**Skill:** `@design-log` (implemented — append conventions, catch-up mode, synthesis rules).

---

## 3. End-to-end workflow

```text
┌─────────────────────────────────────────────────────────────────┐
│ 1. DESIGN CONSULTATION (@design-consultant)                     │
│    design.yaml, constraints.md, architecture, openQuestions   │
│    Output: IC choices per block (MPN intent)                    │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. IC INTAKE (@component-select IC mode)                        │
│    LCSC, fetch-part, bom-targets (ICs only), design-log/ic-*    │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. DATASHEET RESEARCH (@datasheet-research) — per IC, parallel  │
│    extract-datasheet → research/<mpn>/                          │
│    passives-required.md (roles/values, LCSC TBD)              │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. USER DRAWS SCHEMATIC (KiCad — human only)                    │
│    @schematic-draw gives briefs; the agent never draws          │
│    Generic C/R/L symbols OK; ALL passives get value fields      │
│    ICs use global: symbols from library                         │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. SCHEMATIC REVIEW (@schematic-review)                         │
│    dump-design-context + verify-erc + value audit + intent diff │
│    Gate: topology OK, ERC clean or explained, values present    │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. PASSIVE FINALIZE (@component-select passive mode)             │
│    LCSC for passives, bom-targets update, design-log/passive-*  │
└─────────────────────────────────────────────────────────────────┘

design-log/ updated continuously at steps 1–6
```

### Gate checklist before passive LCSC pass

- [ ] Consultant `openQuestions` blocking topology are resolved or explicitly deferred
- [ ] All ICs on schematic match `bom-targets` / `ic-selection.md`
- [ ] `dump-design-context` run on **saved** schematic (note timestamp)
- [ ] ERC run; errors fixed or documented with waiver rationale
- [ ] Every passive ref has a value field
- [ ] Critical passives (strapping, sense, feedback) match `research/*/passives-required.md`

---

## 4. Project directory layout

All paths relative to `<projectDir>` (configured in `kicad-cursor.yaml`).

```text
my-board/
  my-board.kicad_pro
  my-board.kicad_sch
  my-board.kicad_pcb

  design.yaml              # Intent: rails, blocks, constraints, openQuestions
  constraints.md           # Schematic/PCB rules, naming, verification
  bom-targets.yaml         # ICs first (passives added after review)

  datasheets/
    bq25619.pdf
    extracted/
      bq25619/
        index.md
        tables/
        pages/
        images/

  research/
    BQ25619/
      overview.md
      pins.md
      passives-required.md
      interfaces.md

  design-log/
    decisions.md
    open-questions.md
    ic-selection.md
    passive-bom.md
    architecture.md
    reviews/
    context-snapshots.md

  design-context/          # Generated — do not hand-edit
    system-map.md
    open-questions.md
    as-built.yaml
    manifest.yaml
```

Copy starter metadata from [examples/kicad-project-template](../examples/kicad-project-template/README.md), which now ships `research/_template/` and `design-log/` starter files.

### `bom-targets.yaml` shape

```yaml
library: global
path: ${GLOBAL}

parts:
  - symbol: BQ25619
    mpn: BQ25619
    lcsc: Cxxxxxx
    role: battery charger
    status: ic-locked

  - symbol: C0402
    ref: C12
    value: 100nF
    role: REGN bypass
    status: value-only          # At review — value set, LCSC TBD

  - symbol: C0402
    ref: C12
    value: 100nF
    lcsc: Cxxxxxx
    role: REGN bypass
    status: passive-locked      # After passive pass
```

---

## 5. Tool mapping

### 5.1 Step runner (`@kicad-step`)

| Step | Role(s) | Notes |
|------|---------|-------|
| `extract-datasheet` | Research | PDF → `datasheets/extracted/` |
| `fetch-part` | Component | IC intake + passive finalize |
| `fix-symbol-lib` | Component | After fetch-part |
| `dump-design-context` | Review | Always before connectivity review |
| `verify-erc` | Review | **Required** in formal review |
| `verify-drc` | — | Schematic phase: optional; PCB phase later |
| `test-ipc`, `draw-board-outline` | — | PCB phase; not schematic workflow |

`run-block` is retired (moved to `retiredSteps:` in `steps.yaml`) — agents no longer generate schematic content.

### 5.2 Konnect MCP (`@konnect`)

| Allowed (schematic phase) | Forbidden |
|---------------------------|-----------|
| `download_jlcpcb_database` | `add_schematic_component` |
| `get_jlcpcb_part`, `search_jlcpcb_parts` | Schematic wiring / placement toolsets |
| `get_jlcpcb_database_stats` | PCB placement/routing (deferred) |
| Read-only schematic/project tools if needed for context | Any tool that modifies `.kicad_sch` |

**Primary schematic context path:** `dump-design-context` (kicad-cli netlist) — reliable, no image processing.

### 5.3 Human (KiCad)

- Create/edit schematic and symbols on sheet
- Save before `dump-design-context` or `verify-erc`
- Assign value fields to all passives before review

---

## 6. Risks and mitigations

### Too many roles in one chat

Agents drift across consultant / research / component / review. **Mitigation:** One `@skill` per session; each skill lists explicit **will not** actions.

### Pin walkthrough token cost

Full-chip walkthroughs (e.g. 36-channel LED driver) exhaust context. **Mitigation:** Tiered output (overview → pin groups → deep dive on request); persist to `research/<mpn>/`; always use extracted tables.

### Consultant vs reviewer overlap

Both critique the design. **Mitigation:** Consultant = “should we?” before schematic; Reviewer = “did we?” on saved schematic with refs/nets and ERC.

### Stale design context

Schematic changed since last dump. **Mitigation:** Review skill mandates fresh `dump-design-context`; log timestamp in `design-log/context-snapshots.md`; compare to `.kicad_sch` mtime.

### Konnect scope creep

Repo skills previously mentioned schematic placement (`block-draft`, `@konnect` wiring). **Mitigation (done):** `block-draft` and `schematic-design` retired in favor of `@schematic-draw` (human briefs) and `@schematic-review`; `@konnect` rewritten read-only; cursor rule states agents never edit schematics.

### Placeholder passives without values

User draws generic `C0402` with empty value. **Mitigation:** Review gate requires value fields; research `passives-required.md` lists critical values; flag `TBD` on strapping/feedback.

### ERC skipped

Agent marks review complete without ERC. **Mitigation:** `schematic-review` skill checklist requires `verify-erc` output in review report.

---

## 7. Implementation plan

### Phase 0 — Align repo with this document

- [x] External project model (`kicad-cursor.yaml`, examples template)
- [x] `extract-datasheet`, `dump-design-context`, `fetch-part`, `verify-erc` steps
- [x] This plan document
- [x] Link from README and usage.md

### Phase 1 — Principles in agent config

- [x] Update `.cursor/rules/kicad-cursor.mdc`: no schematic editing; IC-before-passive selection; role table
- [x] Rewrite `@konnect` skill: read-only for schematics; JLC + context only
- [x] Retire `@block-draft` and `@schematic-design`; `run-block` moved to `retiredSteps:` and dropped from `run_step.py`
- [x] Clarify `@design-verify` vs `@schematic-review` (ad-hoc check vs review that always runs ERC)

### Phase 2 — Project templates

- [x] `examples/kicad-project-template/design-log/` with starter files (+ `reviews/README.md` report template)
- [x] `examples/kicad-project-template/research/_template/` (overview, pins, passives-required, interfaces)
- [x] `bom-targets.yaml` example with `status` field (`ic-locked` / `value-only` / `passive-locked`)
- [x] Extend `constraints.md` with value-field, selection-order, and review gate rules

### Phase 3 — Skills

- [x] `design-consultant` — new
- [x] `datasheet-research` — new
- [x] `component-select` — refactored into mode A (IC) / mode B (passive) with entry gate
- [x] `schematic-review` — new (dump + ERC + value audit + intent diff + report)
- [x] `design-log` — append conventions, ownership table, catch-up mode
- [x] `schematic-draw` — drawing briefs for the human (replaces `block-draft` / `schematic-design`)

### Phase 4 — Documentation and cleanup

- [x] `docs/workflow.md` — user-facing shortened guide derived from this plan
- [x] Remove stale references to Konnect schematic placement in README, usage.md, setup.md
- [x] PCB workflow placeholder — `docs/workflow.md` "PCB layout — deferred"; `@pcb-layout` marked deferred

### Deferred

- PCB layout specialist roles
- Konnect PCB toolsets (placement, routing) — only after schematic workflow is stable
- Automated passive value suggestion from netlist (optional future step)

---

## 8. Skill inventory (current → planned)

| Skill | Outcome |
|-------|---------|
| `kicad-project` | Kept — points to `workflow.md` / this plan, layout and role table added |
| `konnect` | **Rewritten** — read-only schematic context + JLC DB; forbidden-tool table |
| `component-select` | **Refactored** — mode A (IC intake) / mode B (passive finalize) with entry gate |
| `kicad-step` | Kept — step table annotated by role; `run-block` marked retired |
| `design-verify` | Kept for ad-hoc ERC/DRC; comparison table vs `schematic-review` |
| `block-draft` | **Retired** — superseded by `schematic-draw` |
| `schematic-design` | **Retired** — split into `schematic-draw` (human briefs) + `schematic-review` |
| `pcb-layout` | **Deferred** — marked as such in the skill front matter |
| `design-consultant` | **Added** |
| `datasheet-research` | **Added** |
| `schematic-review` | **Added** |
| `design-log` | **Added** |
| `schematic-draw` | **Added** — drawing guidance for the human |

---

## 9. Open questions (for future plan revisions)

- Should hierarchical sheets trigger per-sheet or full-design review passes?
- ERC warning policy: zero warnings, or documented waivers only?
- Electromechanical parts (connectors, switches): IC intake phase or separate “mechanical intake”?
- When to run first `dump-design-context` — only at review, or optional mid-draw sanity check?
- Konnect version pin: minimum v0.3.0 for `download_jlcpcb_database`?

---

## 10. References

### Prior conversations (workflow patterns)

| Topic | Conversation |
|-------|----------------|
| Power architecture, BQ25619 pin walkthrough, IC-to-IC paths | [Targeted electrical engineering concepts](c8465072-d3ce-41cb-8888-bfc3ed2d9370) |
| IS31FL3236A pin-by-pin, grouped outputs | [LEDs and drivers discussion](cecacd34-7cc6-4cd8-9cd1-d12475b7fc4c) |
| `design.yaml` open questions, display power gaps | [Extract skill on SSD1315 PDF](c5348864-71c8-4512-8836-5638828976cd) |
| Schematic maturity gates, passive BOM timing | [PCB design next steps](cb361dd1-4829-431d-9bba-c27f41de54b0) |
| `dump-design-context` design | [PCB design next steps](cb361dd1-4829-431d-9bba-c27f41de54b0) |
| JLC search, fetch-part, design-decisions | [Low current RGB LEDs](d43950d5-c367-48e9-9f8f-5ba59542108b) |
| ERC/connectivity review | [Schematic errors resolution](6c34d766-232f-434f-8a38-8fad8f1292f8) |
| Passive inventory across conversations | [Passive type identification](2a8c02ba-7a26-4771-a171-1010b8a43692) |

### Repo docs

- [setup.md](setup.md) — KiCad, Konnect, JLC database
- [usage.md](usage.md) — project configuration
- [steps.md](steps.md) — step catalog philosophy
