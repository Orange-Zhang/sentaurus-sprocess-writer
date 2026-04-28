# Example Decks

This folder is for small, synthetic examples that are safe to publish and for local private examples that should remain ignored by git.

## Public Example

- `minimal_oxidation_implant.cmd`: a tiny, synthetic SProcess-style deck used to demonstrate parser, renderer, and analysis workflows. It is not calibrated, not a production process, and not an official Synopsys example.

## Local Examples

You can place licensed official examples or private process decks here for local analysis. Keep them out of public git history unless you have explicit redistribution rights.

Suggested ignored local filenames include:

- `ldmos_*`
- `*_official_*`
- copied tutorial PDFs or HTML pages
- generated TDR, PLX, mesh, and log files

## Regenerating Demo Outputs

```powershell
python scripts\render_sprocess_cross_section.py references\examples\minimal_oxidation_implant.cmd --out references\examples\minimal_oxidation_implant.svg
python scripts\render_sprocess_cross_section.py references\examples\minimal_oxidation_implant.cmd --analysis-out references\examples\minimal_oxidation_implant_analysis.md
```

SVG and analysis outputs are generated artifacts and are ignored by default.
