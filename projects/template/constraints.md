# PCB / schematic constraints

## Board

- Default 2-layer unless design.yaml says otherwise
- Board outline defined in PCB editor or via IPC MCP
- Keep mounting holes ≥ 3.2 mm drill unless specified

## Schematic

- Use `global:` library for all passives and LCSC parts where possible
- Net names: uppercase with underscores (`V3V3`, `I2C_SDA`, `ESP32_EN`)
- One GND symbol style per sheet; tie all grounds
- Decoupling: 100 nF per IC power pin within 3 mm on PCB (0402 default)
- Add bulk cap (4.7–10 µF) per rail near regulator output

## Footprints

- Footprint field format: `global:<footprint_name>`
- After `fetchPart`, verify symbol library file is valid (see scripts/fix-symbol-lib.py)

## Design verification

- Run ERC after schematic changes
- Run DRC after PCB changes
- Agent must not mark work complete until both pass or violations are explained

## KiCad paths (Windows)

- KiCad 10 config: `%APPDATA%/kicad/10.0/`
- Global env var: `GLOBAL=C:\Users\Elli Furedy\projects\global-kicad-lib\`
- CLI: `"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"`
