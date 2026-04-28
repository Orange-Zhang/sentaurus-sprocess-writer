# Publication Checklist

Use this checklist before pushing the repository to GitHub.

## Repository Content

- [ ] Keep `SKILL.md`, `README.md`, `NOTICE.md`, `SECURITY.md`, `LICENSE`, `agents/`, `scripts/`, and safe public `references/`.
- [ ] Do not publish `references/sprocess-user-guide/` unless redistribution is explicitly allowed.
- [ ] Do not publish official tutorial PDFs, HTML files, or copied vendor template decks.
- [ ] Do not publish private process recipes, calibration data, generated TDR/PLX files, or simulation logs.
- [ ] Keep public examples synthetic and clearly marked as non-calibrated demos.

## Privacy And Secrets

- [ ] Search for API keys, tokens, passwords, license-server names, local usernames, and absolute paths.
- [ ] Review `git status --ignored` before the first commit.
- [ ] Review generated files separately; do not rely on filenames alone.

Suggested checks:

```powershell
rg -n -i "api[_-]?key|secret|token|password|bearer|authorization|license|lm_license|[A-Z]:\\\\|/Users/" .
git status --ignored
```

## Copyright

- [ ] Confirm every committed example is original or redistributable.
- [ ] Keep proprietary manuals and extracted text local.
- [ ] Keep product names factual and include trademark/disclaimer language.
- [ ] Use the repository license only for original project code and text.

## Validation

```powershell
python -m py_compile scripts\render_sprocess_cross_section.py scripts\extract_pdf_reference.py
python scripts\render_sprocess_cross_section.py references\examples\minimal_oxidation_implant.cmd --analysis-out references\examples\minimal_oxidation_implant_analysis.md
python scripts\render_sprocess_cross_section.py references\examples\minimal_oxidation_implant.cmd --out references\examples\minimal_oxidation_implant.svg
```
