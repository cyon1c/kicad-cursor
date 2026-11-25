"""Extract a datasheet PDF into agent-readable markdown, images, and YAML tables.

Output layout (when projectDir is configured):

  <projectDir>/datasheets/extracted/<pdf-stem>/
    index.md
    manifest.yaml
    pages/
    tables/
    images/
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
import pymupdf4llm
import yaml

from kicad_cursor_config import addProjectArgs, projectDatasheetsDir, resolveProjectDir

# Adobe Symbol / SymbolMT PUA codepoints seen in ST datasheets.
SYMBOL_FONT_MAP = {
    "\uf020": " ",
    "\uf02d": "-",
    "\uf02e": ".",
    "\uf044": "\u0394",  # Delta
    "\uf057": "\u03a9",  # Omega
    "\uf06d": "\u03bc",  # mu
    "\uf0b0": "\u00b0",  # degree
    "\uf0b1": "\u00b1",  # plus-minus
}

SUBSCRIPT_SIZE_RATIO = 0.88
SUBSCRIPT_X_GAP = 12.0

# Typographic subscript artifacts in ST datasheets after span merge.
ELECTRICAL_REWRITES = [
    (re.compile(r"\bI RM\b"), "IRM"),
    (re.compile(r"\bV BR\b"), "VBR"),
    (re.compile(r"\bV CL\b"), "VCL"),
    (re.compile(r"\bV F\b"), "VF"),
    (re.compile(r"\bI PP\b"), "IPP"),
    (re.compile(r"\bT L\b"), "TL"),
    (re.compile(r"V BUSand"), "VBUS and"),
    (re.compile(r"V BUS\b"), "VBUS"),
    (re.compile(r"Δ C"), "ΔC"),
    (re.compile(r"V\(1\) PP"), "VPP(1)"),
    (re.compile(r"V = ([0-9.]+ V) RM\b"), r"VRM = \1"),
    (re.compile(r"V = ([0-9.]+ V)RM\b"), r"VRM = \1"),
    (re.compile(r"I = ([0-9.]+ mA) R\b"), r"IR = \1"),
    (re.compile(r"I = ([0-9.]+ mA)R\b"), r"IR = \1"),
    (re.compile(r"I = ([0-9.]+ mA) F\b"), r"IF = \1"),
    (re.compile(r"I = ([0-9.]+ mA)F\b"), r"IF = \1"),
    (re.compile(r"I = ([0-9.]+ A, 8/20 µs) ?PP\b"), r"IPP = \1"),
    (re.compile(r"V = ([0-9.]+ V) R\b"), r"VR = \1"),
    (re.compile(r"V = ([0-9.]+ V)R\b"), r"VR = \1"),
    (re.compile(r"8/20 µsPP"), r"8/20 µs"),
    (re.compile(r"8/20 μsPP"), r"8/20 μs"),
    (re.compile(r"I = ([0-9.]+ A, 8/20 [µμ]s)\b"), r"IPP = \1"),
    (re.compile(r"between V and GNDBUS"), "between VBUS and GND"),
    (re.compile(r"andGND\b"), "and GND"),
    (re.compile(r"between I/O andGND"), "between I/O and GND"),
    (re.compile(r"Capacitancebetween"), "Capacitance between"),
    (re.compile(r"voltagebetween"), "voltage between"),
]


def mapSymbolChars(text: str) -> str:
    if not text:
        return text
    out: list[str] = []
    for ch in text:
        out.append(SYMBOL_FONT_MAP.get(ch, ch))
    return "".join(out)


def fixSplitSubscriptSuffix(text: str) -> str:
    # PDFs sometimes emit "i" + "/o-GND" instead of "i/o-GND".
    return re.sub(r"i/o(?=-)", "i/o", text.replace("i\n/o", "i/o").replace("i/o", "i/o"))


def mergeAdjacentSubscriptSpans(spans: list[dict]) -> str:
    """Merge typographic subscripts in a line into readable electrical symbols."""
    if not spans:
        return ""

    ordered = sorted(spans, key=lambda s: (round(s["bbox"][1], 1), s["bbox"][0]))
    lines: list[list[dict]] = []
    for span in ordered:
        if not lines:
            lines.append([span])
            continue
        prevY = round(lines[-1][0]["bbox"][1], 1)
        curY = round(span["bbox"][1], 1)
        if abs(curY - prevY) <= 2.5:
            lines[-1].append(span)
        else:
            lines.append([span])

    mergedLines: list[str] = []
    for lineSpans in lines:
        lineSpans.sort(key=lambda s: s["bbox"][0])
        baseSize = max(s["size"] for s in lineSpans)
        parts: list[str] = []
        lastSpan: dict | None = None
        for span in lineSpans:
            text = mapSymbolChars(span["text"])
            if not text:
                continue
            if (
                parts
                and lastSpan
                and span["size"] < baseSize * SUBSCRIPT_SIZE_RATIO
                and span["bbox"][0] - lastSpan["bbox"][2] < SUBSCRIPT_X_GAP
            ):
                parts[-1] = parts[-1] + text
            else:
                parts.append(text)
            lastSpan = span
        mergedLines.append("".join(parts))

    return fixSplitSubscriptSuffix("\n".join(mergedLines))


def normalizeElectricalNotation(text: str) -> str:
    for pattern, repl in ELECTRICAL_REWRITES:
        text = pattern.sub(repl, text)
    return text


def normalizeCellText(raw: str | None) -> str:
    if not raw:
        return ""
    text = mapSymbolChars(raw)
    text = fixSplitSubscriptSuffix(text)
    text = re.sub(r"([A-Za-z])\n([A-Za-z0-9/\-]+)", r"\1\2", text)
    text = re.sub(r"(\d)\n\.", r"\1.", text)
    text = re.sub(r"(\d{2,})\n\.", lambda m: f"0.{m.group(1).lstrip('0') or '0'}.", text)
    text = re.sub(r"\s+", " ", text).strip()
    return normalizeElectricalNotation(text)


def spansInRect(page: pymupdf.Page, rect: pymupdf.Rect) -> list[dict]:
    hits: list[dict] = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                sb = pymupdf.Rect(span["bbox"])
                if sb.intersects(rect):
                    hits.append(
                        {
                            "text": span.get("text", ""),
                            "font": span.get("font", ""),
                            "size": float(span.get("size", 0)),
                            "bbox": span["bbox"],
                        }
                    )
    return hits


def extractCellFromBbox(page: pymupdf.Page, bbox: tuple[float, float, float, float]) -> str:
    rect = pymupdf.Rect(bbox)
    spans = spansInRect(page, rect)
    if spans:
        return normalizeCellText(mergeAdjacentSubscriptSpans(spans))
    return ""


def normalizeTableRows(page: pymupdf.Page, table) -> list[list[str]]:
    rows: list[list[str]] = []
    for tableRow in table.rows:
        row = [extractCellFromBbox(page, cell) if cell else "" for cell in tableRow.cells]
        rows.append(row)
    if any(any(cell for cell in row) for row in rows):
        return dropDuplicateHeaderRows(rows)

    fallback = table.extract()
    return dropDuplicateHeaderRows(
        [[normalizeCellText(cell or "") for cell in row] for row in fallback]
    )


def dropDuplicateHeaderRows(rows: list[list[str]]) -> list[list[str]]:
    if len(rows) < 2:
        return rows
    header = list(rows[0])
    cleaned: list[list[str]] = []
    for row in rows[1:]:
        first = normalizeCellText(row[0] if row else "")
        second = normalizeCellText(row[1] if len(row) > 1 else "")
        if first.lower() == "symbol" and second.lower() == "parameter":
            if len(row) >= len(header):
                header = [
                    header[i] if i < len(header) and header[i] else normalizeCellText(row[i])
                    for i in range(len(row))
                ]
            continue
        cleaned.append(row)
    return [header] + cleaned


def guessTableTitle(page: pymupdf.Page, tableBbox: pymupdf.Rect) -> str:
    probe = pymupdf.Rect(tableBbox.x0, max(0, tableBbox.y0 - 28), tableBbox.x1, tableBbox.y0)
    text = extractCellFromBbox(page, probe)
    if text:
        return text
    return ""


# Windows MAX_PATH is 260; keep table filenames well under that with the output dir.
MAX_TABLE_SLUG_LEN = 80


def globalImageStagingRoot() -> Path:
    """Path without spaces for pymupdf4llm image writes (md_path replaces spaces with _)."""
    if sys.platform == "win32":
        root = Path(os.environ.get("ProgramData", "C:/ProgramData")) / "kicad-cursor" / "datasheet-extract"
    else:
        root = Path("/tmp/kicad-cursor/datasheet-extract")
    root.mkdir(parents=True, exist_ok=True)
    return root


def imageWriteDirFor(imgDir: Path) -> tuple[Path, Path | None]:
    """Return pymupdf4llm image_path and optional staging dir to copy into imgDir after."""
    resolved = str(imgDir.resolve())
    if " " not in resolved:
        imgDir.mkdir(parents=True, exist_ok=True)
        return imgDir, None

    key = hashlib.sha256(resolved.encode()).hexdigest()[:16]
    stagingImg = globalImageStagingRoot() / key / "images"
    stagingImg.mkdir(parents=True, exist_ok=True)
    return stagingImg, stagingImg


def copyStagedImages(stagingImg: Path, imgDir: Path) -> None:
    imgDir.mkdir(parents=True, exist_ok=True)
    for png in stagingImg.glob("*.png"):
        shutil.copy2(png, imgDir / png.name)


def tableFileName(pageNo: int, title: str, tableIndex: int, usedNames: set[str]) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or f"table-{tableIndex + 1}"
    slug = slug[:MAX_TABLE_SLUG_LEN].rstrip("-") or f"table-{tableIndex + 1}"
    base = f"page-{pageNo:02d}-{slug}"
    name = f"{base}.yaml"
    suffix = 2
    while name in usedNames:
        name = f"{base}-{suffix}.yaml"
        suffix += 1
    usedNames.add(name)
    return name


def rowsToRecords(header: list[str], body: list[list[str]]) -> list[dict[str, str]]:
    keys = [normalizeCellText(h).lower().replace(".", "").replace(" ", "_") for h in header]
    keys = [k or f"col_{i}" for i, k in enumerate(keys)]
    symbolKey = keys[0] if keys else "symbol"
    records: list[dict[str, str]] = []

    for row in body:
        if not any(cell.strip() for cell in row):
            continue

        record: dict[str, str] = {}
        for i, key in enumerate(keys):
            value = normalizeCellText(row[i] if i < len(row) else "")
            if value:
                record[key] = value

        if not record:
            continue

        if record.get(symbolKey, "").lower() == "symbol":
            continue

        if records and not record.get(symbolKey):
            condKey = next((k for k in keys if "condition" in k or k == "col_2"), None)
            if condKey and record.get(condKey):
                prev = records[-1]
                prevCond = prev.get(condKey, "")
                prev[condKey] = f"{prevCond}; {record[condKey]}" if prevCond else record[condKey]
                for key, value in record.items():
                    if key != condKey:
                        prev[f"{key}_2"] = value
                continue

        records.append(record)
    return records


def stripMarkdownPipeTables(text: str) -> str:
    lines = text.splitlines()
    kept: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        kept.append(line)
    return "\n".join(kept)


def fixImagePaths(text: str, pdfStem: str) -> str:
    text = re.sub(
        rf"!\[\]\([^)]*{re.escape(pdfStem)}[^)]*?/([^/)]+)\)",
        r"![](../images/\1)",
        text,
    )
    text = re.sub(r"!\[\]\([^)]*/images/([^/)]+)\)", r"![](../images/\1)", text)
    return text


def appendPageTableLinks(pageText: str, tableLinks: list[tuple[str, str]]) -> str:
    if not tableLinks:
        return pageText
    pageText = stripMarkdownPipeTables(pageText)
    lines = [pageText.rstrip(), "", "## Structured tables", ""]
    for title, relPath in tableLinks:
        lines.append(f"- [{title}]({relPath})")
    lines.append("")
    return "\n".join(lines)


def postProcessMarkdown(text: str) -> str:
    text = mapSymbolChars(text)
    text = fixSplitSubscriptSuffix(text)
    text = re.sub(r"([A-Za-z])\n([A-Za-z0-9/\-]+)", r"\1\2", text)
    text = normalizeElectricalNotation(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def sha256File(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validatePdf(path: Path) -> None:
    header = path.read_bytes()[:8]
    if not header.startswith(b"%PDF"):
        raise ValueError(f"{path.name} is not a PDF (got {header[:40]!r})")


def extractDatasheet(pdfPath: Path, outDir: Path, dpi: int = 200) -> dict:
    validatePdf(pdfPath)
    outDir.mkdir(parents=True, exist_ok=True)
    imgDir = outDir / "images"
    pagesDir = outDir / "pages"
    tablesDir = outDir / "tables"
    pagesDir.mkdir(exist_ok=True)
    tablesDir.mkdir(exist_ok=True)
    imageWriteDir, imageStaging = imageWriteDirFor(imgDir)

    doc = pymupdf.open(str(pdfPath))

    chunks = pymupdf4llm.to_markdown(
        str(pdfPath),
        page_chunks=True,
        write_images=True,
        image_path=str(imageWriteDir),
        image_format="png",
        dpi=dpi,
        header=False,
        footer=False,
    )

    if imageStaging is not None:
        copyStagedImages(imageStaging, imgDir)

    pageSummaries: list[dict] = []
    tableSummaries: list[dict] = []
    pageTableLinks: dict[int, list[tuple[str, str]]] = {}
    usedTableNames: set[str] = set()

    for pageIndex in range(doc.page_count):
        page = doc[pageIndex]
        pageNo = pageIndex + 1
        pageText = postProcessMarkdown(chunks[pageIndex]["text"]) if pageIndex < len(chunks) else ""
        pageText = fixImagePaths(pageText, pdfPath.stem)
        pageFile = pagesDir / f"page-{pageNo:02d}.md"

        found = page.find_tables()
        if found:
            for tableIndex, table in enumerate(found.tables):
                rows = normalizeTableRows(page, table)
                if not rows:
                    continue

                header = [normalizeCellText(h) for h in rows[0]]
                body = [[normalizeCellText(c) for c in row] for row in rows[1:]]
                title = guessTableTitle(page, pymupdf.Rect(table.bbox))
                tableName = tableFileName(pageNo, title, tableIndex, usedTableNames)
                tablePath = tablesDir / tableName

                payload = {
                    "source": pdfPath.name,
                    "page": pageNo,
                    "title": title or f"Table {tableIndex + 1}",
                    "header": header,
                    "rows": body,
                    "records": rowsToRecords(header, body),
                }
                tablePath.write_text(
                    yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
                tableSummaries.append(
                    {
                        "page": pageNo,
                        "title": payload["title"],
                        "file": f"tables/{tableName}",
                        "rowCount": len(body),
                    }
                )
                pageTableLinks.setdefault(pageNo, []).append(
                    (payload["title"], f"../tables/{tableName}")
                )

        pageText = appendPageTableLinks(pageText, pageTableLinks.get(pageNo, []))
        pageFile.write_text(pageText, encoding="utf-8")
        pageSummaries.append({"page": pageNo, "file": f"pages/{pageFile.name}", "chars": len(pageText)})

    images = sorted(imgDir.glob("*.png"))

    manifest = {
        "source": pdfPath.name,
        "sourcePath": str(pdfPath).replace("\\", "/"),
        "sha256": sha256File(pdfPath),
        "extractedAt": datetime.now(timezone.utc).isoformat(),
        "pageCount": doc.page_count,
        "imageCount": len(images),
        "tableCount": len(tableSummaries),
        "pages": pageSummaries,
        "tables": tableSummaries,
        "notes": [
            "Tables are stored as YAML with span-aware symbol normalization.",
            "Electrical symbols merge typographic subscripts (e.g. Ci/o-GND, ΔCi/o-GND).",
            "Prefer tables/*.yaml over markdown pipe tables for specs.",
        ],
    }
    (outDir / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    indexLines = [
        f"# {pdfPath.stem} — extracted datasheet",
        "",
        f"- Source: `{pdfPath.name}`",
        f"- Pages: {doc.page_count}",
        f"- Tables: {len(tableSummaries)}",
        f"- Images: {len(images)}",
        "",
        "## Pages",
        "",
    ]
    indexLines.extend(f"- [Page {p['page']}]({p['file']})" for p in pageSummaries)
    indexLines.extend(["", "## Tables", ""])
    indexLines.extend(
        f"- [Page {t['page']}: {t['title']}]({t['file']}) ({t['rowCount']} rows)"
        for t in tableSummaries
    )
    (outDir / "index.md").write_text("\n".join(indexLines) + "\n", encoding="utf-8")

    doc.close()
    return manifest


def resolvePdf(projectDir: Path | None, pdfArg: str | None) -> Path:
    if pdfArg:
        path = Path(pdfArg)
        if not path.is_absolute() and projectDir is not None:
            candidate = projectDir / path
            if candidate.is_file():
                return candidate
        if not path.is_absolute():
            path = Path.cwd() / path
        return path

    if projectDir is None:
        raise ValueError("Provide --pdf or --project-dir with --all")

    dsDir = projectDatasheetsDir(projectDir)
    pdfs = sorted(p for p in dsDir.glob("*.pdf") if p.is_file())
    if not pdfs:
        raise FileNotFoundError(f"No PDFs in {dsDir}")
    if len(pdfs) == 1:
        return pdfs[0]
    raise ValueError(f"Multiple PDFs in {dsDir}; pass --pdf explicitly")


def outputDirFor(pdfPath: Path, projectDir: Path | None) -> Path:
    if projectDir is not None:
        return projectDatasheetsDir(projectDir) / "extracted" / pdfPath.stem
    return pdfPath.parent / "extracted" / pdfPath.stem


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    addProjectArgs(parser)
    parser.add_argument("--pdf", help="Path to PDF (relative to project or absolute)")
    parser.add_argument("--all", action="store_true", help="Extract every PDF in project datasheets/")
    parser.add_argument("--dpi", type=int, default=200, help="Image render DPI")
    parser.add_argument("--out", type=Path, help="Override output directory")
    args = parser.parse_args()

    try:
        if args.all:
            projectDir = resolveProjectDir(args.project_dir, args.project)
            dsDir = projectDatasheetsDir(projectDir)
            targets = sorted(p for p in dsDir.glob("*.pdf") if p.is_file())
        else:
            if not args.pdf:
                raise ValueError("Provide --pdf or use --all")
            if args.project_dir:
                projectDir = resolveProjectDir(args.project_dir, args.project)
            else:
                try:
                    projectDir = resolveProjectDir()
                except ValueError:
                    projectDir = None
            targets = [resolvePdf(projectDir, args.pdf)]

        for pdfPath in targets:
            outDir = args.out if args.out and len(targets) == 1 else outputDirFor(pdfPath, projectDir)
            manifest = extractDatasheet(pdfPath, outDir, dpi=args.dpi)
            print(f"extracted: {pdfPath.name}")
            print(f"  out: {outDir}")
            print(f"  pages={manifest['pageCount']} tables={manifest['tableCount']} images={manifest['imageCount']}")
        return 0
    except (ValueError, FileNotFoundError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
