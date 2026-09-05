"""Dump schematic design context from KiCad files for agent review.

Exports authoritative connectivity via kicad-cli netlist, plus hierarchy and
BOM fields parsed from schematic sources. Output is explicitly *as-built*
observation — not validated requirements.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from kicad_cursor_config import findProjectFiles, resolveKicadCli, resolveProjectDir

GENERIC_LIB_PATTERNS = (
    re.compile(r"^Connector", re.I),
    re.compile(r"^Switch:", re.I),
    re.compile(r"^Mechanical:", re.I),
)

PLACEHOLDER_VALUE_PATTERNS = (
  re.compile(r"^AudioJack", re.I),
  re.compile(r"^SW_", re.I),
  re.compile(r"^MountingHole", re.I),
  re.compile(r"^LED$", re.I),
  re.compile(r"^Schottky$", re.I),
)


def findKicadCli() -> Path:
    return resolveKicadCli()


def resolveRootSchematic(projectDir: Optional[Path], schematicPath: Optional[Path]) -> Path:
    if schematicPath:
        path = schematicPath.resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Schematic not found: {path}")
        return path

    if projectDir:
        directory = projectDir.resolve()
        if not directory.is_dir():
            raise FileNotFoundError(f"Project directory not found: {directory}")
        schematic, _, _ = findProjectFiles(directory)
        return schematic

    directory = resolveProjectDir()
    schematic, _, _ = findProjectFiles(directory)
    return schematic


def exportNetlistXml(rootSchematic: Path, kicadCli: Path) -> Path:
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as handle:
        outputPath = Path(handle.name)
    result = subprocess.run(
        [
            str(kicadCli),
            "sch",
            "export",
            "netlist",
            "-o",
            str(outputPath),
            "--format",
            "kicadxml",
            str(rootSchematic),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        outputPath.unlink(missing_ok=True)
        raise RuntimeError(f"kicad-cli netlist export failed:\n{result.stderr or result.stdout}")
    return outputPath


def parseHierarchy(rootSchematic: Path) -> list[dict[str, Any]]:
    text = rootSchematic.read_text(encoding="utf-8")
    sheets: list[dict[str, Any]] = []
    for block in re.finditer(r"\(sheet\b", text):
        start = block.start()
        depth = 0
        end = start
        for index in range(start, len(text)):
            if text[index] == "(":
                depth += 1
            elif text[index] == ")":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        chunk = text[start:end]
        nameMatch = re.search(r'\(property "Sheetname" "([^"]*)"', chunk)
        fileMatch = re.search(r'\(property "Sheetfile" "([^"]*)"', chunk)
        pageMatch = re.search(r'\(property "Sheetpage" "([^"]*)"', chunk)
        if not fileMatch:
            continue
        pins: list[dict[str, str]] = []
        for pinMatch in re.finditer(r'\(pin "([^"]+)"\s+(\w+)', chunk):
            pins.append({"name": pinMatch.group(1), "type": pinMatch.group(2)})
        sheets.append(
            {
                "name": nameMatch.group(1) if nameMatch else fileMatch.group(1),
                "file": fileMatch.group(1),
                "page": pageMatch.group(1) if pageMatch else "",
                "pins": pins,
            }
        )
    return sheets


def fieldText(compNode: ET.Element, fieldName: str) -> str:
    for field in compNode.findall("fields/field"):
        if field.attrib.get("name") == fieldName:
            return (field.text or "").strip()
    return ""


def propertyText(compNode: ET.Element, propertyName: str) -> str:
    for prop in compNode.findall("property"):
        if prop.attrib.get("name") == propertyName:
            return (prop.text or "").strip()
    return ""


def lcscFromComponent(compNode: ET.Element) -> str:
    for key in ("LCSC Part", "LCSC Part #", "LCSC"):
        value = fieldText(compNode, key) or propertyText(compNode, key)
        if value:
            return value
    return ""


def sheetNameFromComponent(compNode: ET.Element) -> str:
    sheetPath = compNode.find("sheetpath")
    if sheetPath is not None and sheetPath.attrib.get("names"):
        return sheetPath.attrib["names"]
    return propertyText(compNode, "Sheetname")


def sheetFileFromComponent(compNode: ET.Element, sheetSources: dict[str, str]) -> str:
    direct = propertyText(compNode, "Sheetfile")
    if direct:
        return direct
    sheetName = sheetNameFromComponent(compNode)
    return sheetSources.get(sheetName, "")


def isGenericComponent(libPart: str, value: str, reference: str) -> bool:
    if any(pattern.search(libPart) for pattern in GENERIC_LIB_PATTERNS):
        if libPart.startswith("global:"):
            return False
        return True
    if any(pattern.search(value) for pattern in PLACEHOLDER_VALUE_PATTERNS):
        return True
    if reference.startswith("#"):
        return True
    return False


def isMajorIc(libPart: str, reference: str) -> bool:
    if reference.startswith("#"):
        return False
    if not libPart.startswith("global:"):
        return False
    if re.match(r"^[CRLDQF]", reference):
        return False
    return True


def parseNetlistXml(netlistPath: Path) -> dict[str, Any]:
    root = ET.parse(netlistPath).getroot()
    designNode = root.find("design")
    sheets: list[dict[str, str]] = []
    if designNode is not None:
        for sheet in designNode.findall("sheet"):
            source = ""
            title = sheet.find("title_block/source")
            if title is not None and title.text:
                source = title.text.strip()
            sheets.append(
                {
                    "number": sheet.attrib.get("number", ""),
                    "name": sheet.attrib.get("name", ""),
                    "source": source,
                }
            )

    sheetSources = {sheet["name"]: sheet["source"] for sheet in sheets if sheet["source"]}

    components: list[dict[str, Any]] = []
    for comp in root.findall("components/comp"):
        ref = comp.attrib.get("ref", "")
        valueNode = comp.find("value")
        value = valueNode.text.strip() if valueNode is not None and valueNode.text else ""
        footprintNode = comp.find("footprint")
        footprint = footprintNode.text.strip() if footprintNode is not None and footprintNode.text else ""
        libNode = comp.find("libsource")
        lib = ""
        part = ""
        if libNode is not None:
            lib = libNode.attrib.get("lib", "")
            part = libNode.attrib.get("part", "")
        libId = f"{lib}:{part}" if lib else part
        datasheetNode = comp.find("datasheet")
        datasheet = datasheetNode.text.strip() if datasheetNode is not None and datasheetNode.text else ""
        components.append(
            {
                "reference": ref,
                "value": value,
                "libId": libId,
                "footprint": footprint,
                "lcsc": lcscFromComponent(comp),
                "datasheet": datasheet,
                "sheet": sheetNameFromComponent(comp),
                "sheetFile": sheetFileFromComponent(comp, sheetSources),
                "isGeneric": isGenericComponent(libId, value, ref),
                "isMajorIc": isMajorIc(libId, ref),
            }
        )

    nets: list[dict[str, Any]] = []
    for net in root.findall("nets/net"):
        nodes: list[dict[str, str]] = []
        for node in net.findall("node"):
            nodes.append(
                {
                    "reference": node.attrib.get("ref", ""),
                    "pin": node.attrib.get("pin", ""),
                    "pinFunction": node.attrib.get("pinfunction", ""),
                    "pinType": node.attrib.get("pintype", ""),
                }
            )
        nets.append(
            {
                "name": net.attrib.get("name", ""),
                "code": net.attrib.get("code", ""),
                "nodes": nodes,
            }
        )

    return {"sheets": sheets, "components": components, "nets": nets}


def gpioMapForEsp32(components: list[dict[str, Any]], nets: list[dict[str, Any]]) -> list[dict[str, str]]:
    espRefs = {item["reference"] for item in components if "ESP32" in item.get("value", "") or "ESP32" in item.get("libId", "")}
    if not espRefs:
        return []
    rows: list[dict[str, str]] = []
    for net in nets:
        for node in net["nodes"]:
            if node["reference"] not in espRefs:
                continue
            pinFunction = node.get("pinFunction", "")
            gpioMatch = re.search(r"IO\d+", pinFunction)
            gpio = gpioMatch.group(0) if gpioMatch else pinFunction or node["pin"]
            rows.append(
                {
                    "gpio": gpio,
                    "net": net["name"],
                    "pin": node["pin"],
                }
            )
    rows.sort(key=lambda item: (item["gpio"], item["net"]))
    return rows


def crossSheetSignals(hierarchy: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pinOwners: dict[str, list[str]] = defaultdict(list)
    for sheet in hierarchy:
        for pin in sheet.get("pins", []):
            pinOwners[pin["name"]].append(sheet["name"])
    shared: list[dict[str, Any]] = []
    for pinName, owners in sorted(pinOwners.items()):
        if len(owners) > 1:
            shared.append({"signal": pinName, "sheets": owners})
    return shared


def buildOpenQuestions(parsed: dict[str, Any], hierarchy: list[dict[str, Any]]) -> list[dict[str, str]]:
    questions: list[dict[str, str]] = []
    components = parsed["components"]
    nets = parsed["nets"]
    passivesMissingLcsc: dict[str, int] = defaultdict(int)

    for comp in components:
        if comp["reference"].startswith("#"):
            continue
        if comp["isGeneric"]:
            if comp["libId"].startswith("Mechanical:"):
                continue
            questions.append(
                {
                    "id": f"placeholder-{comp['reference']}",
                    "category": "part_selection",
                    "question": f"{comp['reference']} ({comp['value']}) uses a generic symbol — confirm LCSC part and footprint before PCB.",
                    "source": f"{comp['sheetFile']}:{comp['reference']}",
                }
            )
        elif comp["isMajorIc"] and not comp["lcsc"]:
            questions.append(
                {
                    "id": f"missing-lcsc-{comp['reference']}",
                    "category": "bom",
                    "question": f"{comp['reference']} ({comp['value']}) has no LCSC part number in schematic fields.",
                    "source": f"{comp['sheetFile']}:{comp['reference']}",
                }
            )
        elif re.match(r"^[CR]", comp["reference"]) and not comp["lcsc"]:
            passivesMissingLcsc[comp["sheetFile"] or "unknown"] += 1
        if comp["reference"].startswith("NTC") and not comp["value"]:
            questions.append(
                {
                    "id": f"ntc-value-{comp['reference']}",
                    "category": "component_value",
                    "question": f"{comp['reference']} has no value — confirm NTC resistance curve from BQ25619 TS network.",
                    "source": f"{comp['sheetFile']}:{comp['reference']}",
                }
            )

    if passivesMissingLcsc:
        total = sum(passivesMissingLcsc.values())
        bySheet = ", ".join(f"{sheet}: {count}" for sheet, count in sorted(passivesMissingLcsc.items()))
        questions.append(
            {
                "id": "passive-bom-incomplete",
                "category": "bom",
                "question": f"{total} resistors/capacitors have no LCSC part ({bySheet}). Fill BOM before PCB.",
                "source": "netlist",
            }
        )

    autoNets = [net for net in nets if net["name"].startswith("Net-(")]
    if autoNets:
        sample = ", ".join(net["name"] for net in autoNets[:8])
        extra = f" (+{len(autoNets) - 8} more)" if len(autoNets) > 8 else ""
        questions.append(
            {
                "id": "auto-net-names",
                "category": "net_naming",
                "question": f"{len(autoNets)} nets still use KiCad auto-names ({sample}{extra}). Review before treating netlist as documentation.",
                "source": "netlist",
            }
        )

    unconnected = [net for net in nets if net["name"].startswith("unconnected-")]
    if unconnected:
        questions.append(
            {
                "id": "explicit-nc-pins",
                "category": "connectivity",
                "question": f"{len(unconnected)} pins are explicitly marked unconnected — verify these are intentional NC, not missing wiring.",
                "source": "netlist",
            }
        )

    crossSignals = crossSheetSignals(hierarchy)
    if crossSignals:
        preview = ", ".join(item["signal"] for item in crossSignals[:6])
        if len(crossSignals) > 6:
            preview = f"{preview}, …"
        questions.append(
            {
                "id": "cross-sheet-interfaces",
                "category": "system_integration",
                "question": (
                    f"{len(crossSignals)} signals cross hierarchical sheets "
                    f"({preview}) — verify pull-ups, levels, and firmware pin map."
                ),
                "source": "hierarchy",
            }
        )

    questions.append(
        {
            "id": "epistemic-reminder",
            "category": "process",
            "question": "This dump reflects the schematic as-drawn. Run ERC, datasheet review, and system analysis before promoting any item to design rules.",
            "source": "dump_design_context",
        }
    )
    return questions


def summarizeMajorIcs(components: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for comp in components:
        if not comp["isMajorIc"]:
            continue
        rows.append(
            {
                "reference": comp["reference"],
                "value": comp["value"],
                "lcsc": comp["lcsc"] or "—",
                "sheet": comp["sheet"] or "/",
            }
        )
    rows.sort(key=lambda item: item["reference"])
    return rows


def powerRailNets(nets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keywords = ("VBUS", "VCC", "VSYS", "+3V3", "+BATT", "-BATT", "GND", "REGN", "BATT")
    rows: list[dict[str, Any]] = []
    for net in nets:
        name = net["name"]
        shortName = name.split("/")[-1]
        if any(keyword in shortName.upper() for keyword in keywords):
            icNodes = [
                f"{node['reference']}.{node['pinFunction'] or node['pin']}"
                for node in net["nodes"]
                if node["reference"] and not node["reference"].startswith("#")
                and re.match(r"^U", node["reference"])
            ]
            rows.append(
                {
                    "net": name,
                    "nodeCount": len(net["nodes"]),
                    "icConnections": icNodes[:12],
                }
            )
    return rows


def renderSystemMap(
    rootSchematic: Path,
    hierarchy: list[dict[str, Any]],
    parsed: dict[str, Any],
    gpioMap: list[dict[str, str]],
    openQuestions: list[dict[str, str]],
) -> str:
    lines: list[str] = [
        "# System map (as-built)",
        "",
        "> **Status: observation only.** This file is generated from the schematic on disk.",
        "> It describes what is drawn, not what *should* be. See `open-questions.md` before",
        "> treating any detail as a requirement.",
        "",
        f"- **Root schematic:** `{rootSchematic}`",
        f"- **Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"- **Components:** {len(parsed['components'])}",
        f"- **Nets:** {len(parsed['nets'])}",
        "",
        "## Hierarchy",
        "",
    ]
    for sheet in hierarchy:
        pinSummary = ", ".join(pin["name"] for pin in sheet.get("pins", [])) or "—"
        lines.append(f"- **{sheet['name']}** (`{sheet['file']}`) — pins: {pinSummary}")
    lines.extend(["", "## Major ICs", "", "| Ref | Part | LCSC | Sheet |", "|-----|------|------|-------|"])
    for row in summarizeMajorIcs(parsed["components"]):
        lines.append(f"| {row['reference']} | {row['value']} | {row['lcsc']} | {row['sheet']} |")

    lines.extend(["", "## Cross-sheet signals", ""])
    for signal in crossSheetSignals(hierarchy):
        lines.append(f"- **{signal['signal']}** → {', '.join(signal['sheets'])}")

    if gpioMap:
        lines.extend(["", "## ESP32 GPIO map (from netlist)", "", "| GPIO | Net | Pin |", "|------|-----|-----|"])
        for row in gpioMap:
            lines.append(f"| {row['gpio']} | `{row['net']}` | {row['pin']} |")

    lines.extend(["", "## Power rails (selected)", ""])
    for rail in powerRailNets(parsed["nets"]):
        icText = ", ".join(rail["icConnections"]) if rail["icConnections"] else "—"
        lines.append(f"- **{rail['net']}** ({rail['nodeCount']} nodes) — ICs: {icText}")

    placeholderCount = sum(1 for comp in parsed["components"] if comp["isGeneric"] and not comp["reference"].startswith("#"))
    lines.extend(
        [
            "",
            "## Placeholders / generics",
            "",
            f"{placeholderCount} components still use generic or non-LCSC symbols (connectors, switches, passives without C-numbers, etc.).",
            "",
            "## Open questions",
            "",
            f"See `open-questions.md` ({len(openQuestions)} items, including process reminders).",
        ]
    )
    return "\n".join(lines) + "\n"


def renderOpenQuestions(openQuestions: list[dict[str, str]]) -> str:
    lines = [
        "# Open questions",
        "",
        "> Generated from the as-built dump. Each item is a *candidate* review task.",
        "> Resolve against datasheets, ERC, and system intent before closing.",
        "",
    ]
    byCategory: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item in openQuestions:
        if item["id"] == "epistemic-reminder":
            continue
        byCategory[item["category"]].append(item)
    for category in sorted(byCategory):
        lines.append(f"## {category.replace('_', ' ').title()}")
        lines.append("")
        for item in byCategory[category]:
            lines.append(f"- [ ] **{item['id']}** — {item['question']}")
            lines.append(f"  - Source: `{item['source']}`")
        lines.append("")
    lines.extend(
        [
            "## Process",
            "",
            "- [ ] Re-run ERC and resolve errors/warnings",
            "- [ ] Cross-check IC passives against datasheet typical application circuits",
            "- [ ] Promote validated items from `design-rules-draft.yaml` to Konnect only after explicit review",
            "",
        ]
    )
    return "\n".join(lines)


def buildDesignRulesDraft(
    parsed: dict[str, Any],
    hierarchy: list[dict[str, Any]],
    openQuestions: list[dict[str, str]],
) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    for comp in summarizeMajorIcs(parsed["components"]):
        observations.append(
            {
                "id": f"ic-{comp['reference'].lower()}",
                "kind": "component_selection",
                "observed": f"{comp['reference']} = {comp['value']} (LCSC {comp['lcsc']})",
                "source": comp["sheet"],
                "confidence": "high" if comp["lcsc"] != "—" else "medium",
                "status": "unverified",
                "validateBeforePromoting": ["datasheet typical application", "JLC stock and footprint"],
            }
        )
    for signal in crossSheetSignals(hierarchy):
        observations.append(
            {
                "id": f"signal-{signal['signal'].lower()}",
                "kind": "interface",
                "observed": f"Signal {signal['signal']} connects sheets: {', '.join(signal['sheets'])}",
                "source": "hierarchy",
                "confidence": "high",
                "status": "unverified",
                "validateBeforePromoting": ["firmware pin map", "pull-ups and levels"],
            }
        )
    return {
        "status": "draft",
        "promotionPolicy": (
            "Nothing in this file is an enforced design rule. Observations may be wrong. "
            "Promote to Konnect add_design_rule or .konnect/project.json only after "
            "datasheet review and explicit human approval."
        ),
        "verifiedRules": [],
        "processRules": [
            {
                "id": "prefer-global-lib",
                "rule": "Use global: library symbols and footprints for LCSC parts where possible.",
                "status": "policy",
            },
            {
                "id": "dump-before-review",
                "rule": "Re-run dump-design-context after major schematic edits before system review.",
                "status": "policy",
            },
        ],
        "observations": observations,
        "openQuestionIds": [item["id"] for item in openQuestions if item["id"] != "epistemic-reminder"],
    }


def writeOutputs(
    outputDir: Path,
    rootSchematic: Path,
    hierarchy: list[dict[str, Any]],
    parsed: dict[str, Any],
    gpioMap: list[dict[str, str]],
    openQuestions: list[dict[str, str]],
) -> None:
    outputDir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = {
        "kind": "design-context-dump",
        "status": "as-built",
        "epistemicStatus": "observation_not_requirement",
        "generatedAt": timestamp,
        "rootSchematic": str(rootSchematic),
        "projectDir": str(rootSchematic.parent),
        "sourceTool": "dump_design_context.py",
        "connectivitySource": "kicad-cli sch export netlist (kicadxml)",
        "files": {
            "asBuilt": "as-built.yaml",
            "systemMap": "system-map.md",
            "openQuestions": "open-questions.md",
            "designRulesDraft": "design-rules-draft.yaml",
        },
        "promotionPolicy": (
            "Do not treat this dump as requirements. Use open-questions.md to drive review. "
            "Only move validated findings into Konnect design rules."
        ),
    }
    asBuilt = {
        "manifest": manifest,
        "hierarchy": hierarchy,
        "sheets": parsed["sheets"],
        "majorIcs": summarizeMajorIcs(parsed["components"]),
        "components": parsed["components"],
        "nets": parsed["nets"],
        "gpioMap": gpioMap,
        "crossSheetSignals": crossSheetSignals(hierarchy),
        "powerRails": powerRailNets(parsed["nets"]),
    }
    designRulesDraft = buildDesignRulesDraft(parsed, hierarchy, openQuestions)

    (outputDir / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    (outputDir / "as-built.yaml").write_text(
        yaml.safe_dump(asBuilt, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    (outputDir / "system-map.md").write_text(
        renderSystemMap(rootSchematic, hierarchy, parsed, gpioMap, openQuestions),
        encoding="utf-8",
    )
    (outputDir / "open-questions.md").write_text(renderOpenQuestions(openQuestions), encoding="utf-8")
    (outputDir / "design-rules-draft.yaml").write_text(
        yaml.safe_dump(designRulesDraft, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, help="Path to KiCad project directory")
    parser.add_argument("--schematic", type=Path, help="Path to root .kicad_sch file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: <project>/design-context)",
    )
    args = parser.parse_args()

    try:
        rootSchematic = resolveRootSchematic(args.project_dir, args.schematic)
        outputDir = args.output_dir or (rootSchematic.parent / "design-context")
        kicadCli = findKicadCli()
        hierarchy = parseHierarchy(rootSchematic)
        netlistPath = exportNetlistXml(rootSchematic, kicadCli)
        try:
            parsed = parseNetlistXml(netlistPath)
        finally:
            netlistPath.unlink(missing_ok=True)
        gpioMap = gpioMapForEsp32(parsed["components"], parsed["nets"])
        openQuestions = buildOpenQuestions(parsed, hierarchy)
        writeOutputs(outputDir, rootSchematic, hierarchy, parsed, gpioMap, openQuestions)
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Wrote design context to {outputDir}")
    print(f"  components: {len(parsed['components'])}")
    print(f"  nets: {len(parsed['nets'])}")
    print(f"  open questions: {len(openQuestions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
