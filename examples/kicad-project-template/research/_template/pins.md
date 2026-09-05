# <MPN> — pins

Source: `datasheets/extracted/<stem>/tables/*.yaml` (pin table). Group pins that behave identically; do not narrate 36 identical outputs one by one.

## Pin table

| Pin | Name | Type | Function | External parts (by role) | Strapping / config |
|-----|------|------|----------|--------------------------|--------------------|
| 1 | VIN | power in | main supply | bulk cap, decoupling cap | — |
| 2 | EN | digital in | enable | pull-up to VIN | must not float |

Types: `power in`, `power out`, `digital in/out`, `analog in`, `open drain`, `passive`, `NC`.

## Groups

### Power pins

Which pins share a rail, how many decoupling caps, and where bulk goes.

### Control / strapping pins

Every pin that must not float, and what sets its state.

| Pin | Required state | Set by | Consequence if wrong |
|-----|----------------|--------|----------------------|

### <Functional group, e.g. LED sinks / switching node>

Behavior once, then the per-pin exceptions.

## Application circuit decoded

Walk the datasheet's typical application figure against the pin table: for each external component in the figure, say which pin it serves and why it is there.

| Component in figure | Pin | Why |
|---------------------|-----|-----|

## Path to the next IC

How rails and signals leave this chip and reach the next block — the hand-off the schematic must draw.

## Do not

- Assign LCSC numbers here (`@component-select`)
- Recommend placement coordinates or wiring order (`@schematic-draw` gives the user a brief)
