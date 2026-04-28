---
name: sentaurus-sprocess-writer
description: Write, modify, review, and troubleshoot Synopsys Sentaurus SProcess command decks using local SProcess syntax references. Use when Codex needs to generate SProcess .cmd files, translate process-flow intent into SProcess code, add implants/deposition/etch/diffusion/mesh/contact steps, adapt an existing process deck, or consult a provided SProcess PDF/manual converted into references.
---

# Sentaurus SProcess Writer

Use this skill to write and edit Sentaurus SProcess command decks from process intent, existing decks, and local syntax references. Always ground syntax-sensitive work in bundled public references, local user-provided references, or user-provided manual excerpts.

## Operating Mode

1. Clarify the target flow only as much as needed:
   - device/process type
   - dimensionality and coordinate convention
   - starting substrate and wafer orientation
   - materials, masks, implants, thermal steps, etch/deposition steps
   - intended output structure/grid file for downstream SDevice or SVisual
2. Inspect existing decks before generating new code. Preserve local naming conventions, units, mesh settings, comments, and output filenames.
3. Inspect `references/examples/` for similar local decks, especially LDMOS process, device mesh, and contact patterns when the user has provided them.
4. Search local SProcess manual references before using unfamiliar syntax. If `references/sprocess-user-guide/` is absent, ask the user to provide or extract their own licensed local reference.
5. Generate conservative deck edits. Avoid inventing unsupported command options.
6. Include comments that mark major process stages, but do not over-comment obvious one-line commands.
7. After writing code, provide a short validation checklist: syntax areas to verify, expected outputs, and likely run command.

## Local Manual Setup

Before syntax-sensitive work, check whether `references/sprocess-user-guide/INDEX.md` exists.

If it exists:

1. Search `references/sprocess-user-guide/` with `rg` for the relevant command or option.
2. Open only the matching chunks needed for the task.
3. Cite the local chunk filenames in the response when syntax choices depend on them.

If it does not exist, do not silently rely on memory for unfamiliar SProcess syntax. Ask the user which path they prefer:

1. They already have extracted Markdown chunks and can place them under `references/sprocess-user-guide/`.
2. They have a licensed local SProcess manual PDF and want it extracted with `scripts/extract_pdf_reference.py`.
3. They want to continue in draft mode using only public repository examples and later validate against their installed Sentaurus release.

If the user chooses PDF extraction and has not already provided a path:

1. Ask for the local PDF path.
2. Ask the user to confirm that they are allowed to use the manual locally.
3. Extract to `references/sprocess-user-guide/` unless the user requests another output directory.
4. Verify that `references/sprocess-user-guide/INDEX.md` exists.
5. Continue syntax lookup from the extracted chunks.

Use draft mode only for conceptual sketches, simple examples, or when the user explicitly accepts later validation. Draft mode is based on this skill's public instructions, synthetic examples, lightweight command index, and the model's general knowledge. It is suitable for planning and initial skeletons, but not a substitute for syntax verification against the user's installed Sentaurus release and local manual.

When extracting a PDF, remind the user that generated chunks are local-only by default and should not be committed or redistributed unless they have explicit rights.

## Reference Handling

If the user provides a PDF manual:

1. Keep the original PDF outside the skill or place it in `references/source/` only if the user wants a portable local bundle.
2. Convert the PDF into Markdown chunks with `scripts/extract_pdf_reference.py`.
3. Put generated SProcess User Guide chunks under `references/sprocess-user-guide/`.
4. Search chunks with `rg` before loading large sections.
5. Cite the local chunk filenames in your reasoning summary, not external URLs.
6. Treat extracted manual chunks as local-only unless the user confirms redistribution rights.

If local examples exist, cite the example file names when following their organization, naming, or meshing style. Do not assume examples are redistributable.

Run extraction:

```powershell
& "C:\Program Files\Python313\python.exe" scripts\extract_pdf_reference.py --pdf <manual.pdf> --out references\sprocess-user-guide --prefix sprocess-ug
```

The extractor needs either `pypdf` or `PyMuPDF` installed in the active Python environment.

## Writing Pattern

For a new deck, produce this structure unless the user gives a stronger local pattern:

1. Header with purpose, assumptions, and expected outputs.
2. Parameter block for process dimensions, doses, energies, temperatures, and times.
3. Initial substrate/line/grid setup.
4. Geometry and mask definitions.
5. Process sequence:
   - deposition
   - lithography/mask application
   - etch
   - implant
   - diffusion/anneal/oxidation
   - strip/cleanup
6. Remeshing/refinement if needed for junctions, interfaces, or downstream device simulation.
7. Structure save/output statements.

For LDMOS decks, prefer user-provided local examples in `references/examples/` over the generic structure above when they fit the user's target.

## Review Checklist

Before returning SProcess code, check:

- Units are explicit or consistent with the existing deck.
- Mask names are defined before use.
- Material and region names are consistent.
- Implant species, dose, energy, tilt, rotation, and model assumptions are visible.
- Thermal steps include temperature/time/ambient where required.
- Output `.tdr` filenames are predictable and do not overwrite unrelated data.
- Downstream SDevice contact/region expectations are noted if relevant.

## Guardrails

- Do not claim exact SProcess syntax from memory when the local manual is available; search it.
- Use traditional SProcess `.cmd` deck syntax for generated or edited process flows.
- If the manual is not ingested yet, label generated decks as draft syntax and ask for validation against the installed Sentaurus release.
- Do not copy long manual passages into answers. Summarize the relevant command shape and point to local reference chunks.
- Treat process recipes as proprietary research data. Keep generated decks in the user's chosen workspace.
- Do not publish or redistribute Synopsys manuals, official tutorial decks, licensed examples, license files, or private process recipes unless the user explicitly confirms rights.
- For public repository work, keep examples synthetic and authored for the repository; use local proprietary references only as private inputs.
