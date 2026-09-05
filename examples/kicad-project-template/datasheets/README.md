# Datasheets

Store source PDFs here. Run `extract-datasheet` to generate agent-readable output alongside them.

## Layout

```text
datasheets/
  bq25895.pdf                    # source PDF (you add this)
  extracted/
    bq25895/                     # generated — one folder per PDF stem
      index.md                   # start here
      manifest.yaml
      pages/                     # per-page markdown
      tables/                    # structured specs (prefer over pages for numbers)
      images/                    # figures, pinouts
```

**Do not** put extracted output in the kicad-cursor repo. It belongs under your KiCad project folder:

`<projectDir>/datasheets/extracted/<pdf-stem>/`

The `extract-datasheet` step writes there automatically when `projectDir` is configured.

## Extract

```powershell
# Single PDF (path relative to project dir)
uv run python scripts/run_step.py extract-datasheet --pdf datasheets/bq25895.pdf

# All PDFs in datasheets/
uv run python scripts/run_step.py extract-datasheet --all
```

## Reading extracted content

1. Open `extracted/<part>/index.md` first.
2. Use `tables/*.yaml` for electrical specs and limits.
3. Use `pages/*.md` for prose and application notes.
4. Use `images/` for pinouts and reference circuits.

Re-run extraction if you replace the source PDF.
