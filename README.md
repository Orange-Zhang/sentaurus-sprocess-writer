# Sentaurus SProcess Writer Skill

A Codex skill for writing, reviewing, and lightly analyzing traditional Synopsys Sentaurus Process (`sprocess`) command decks.

This project is intended for learning, research discussion, and personal workflow automation. It does not include Synopsys manuals, proprietary tutorial projects, license files, or any private process recipes.

## What It Does

- Guides Codex to write or revise SProcess `.cmd` decks from process-flow intent.
- Encourages syntax checks against local user-provided references instead of model memory.
- Provides helper scripts for:
  - extracting a licensed local PDF manual into searchable Markdown chunks;
  - rendering heuristic SVG cross-section sketches from common deck patterns;
  - generating Markdown analysis reports with masks, implants, thermal steps, and contacts.

The renderer is a review aid, not a process simulator. Always validate final geometry, doping, mesh, and contacts with the actual Sentaurus toolchain and TDR/SVisual inspection.

## Skill Layout

```text
sentaurus-sprocess-writer/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── prompt-patterns.md
│   ├── sprocess-command-index.md
│   └── examples/
│       ├── README.md
│       └── minimal_oxidation_implant.cmd
└── scripts/
    ├── extract_pdf_reference.py
    └── render_sprocess_cross_section.py
```

Large or licensed local references belong outside public git history. See `.gitignore` and `NOTICE.md`.

## Install

Copy this folder into your Codex skills directory:

```powershell
Copy-Item -Recurse . "$env:USERPROFILE\.codex\skills\sentaurus-sprocess-writer"
```

Restart Codex so it reloads skill metadata.

## Optional Dependencies

The core skill instructions do not require Python packages. The helper scripts use optional packages:

```powershell
python -m pip install shapely pypdf
```

For PDF extraction, either `pypdf` or `PyMuPDF` can be used. For optional PNG export from SVG, `cairosvg` plus the native Cairo runtime is required.

## Usage

Ask Codex naturally, or mention the skill name:

```text
Use $sentaurus-sprocess-writer to draft a 2D SProcess deck with silicon substrate setup, oxide deposition, anisotropic etch, boron implant, anneal, and final TDR output.
```

Render a conceptual cross-section from a deck:

```powershell
python scripts\render_sprocess_cross_section.py references\examples\minimal_oxidation_implant.cmd --out references\examples\minimal_oxidation_implant.svg
```

Generate a Markdown analysis report:

```powershell
python scripts\render_sprocess_cross_section.py references\examples\minimal_oxidation_implant.cmd --analysis-out references\examples\minimal_oxidation_implant_analysis.md
```

Extract your own licensed local manual into references:

```powershell
python scripts\extract_pdf_reference.py --pdf <path-to-your-licensed-sprocess-manual.pdf> --out references\sprocess-user-guide --prefix sprocess-ug --pages-per-chunk 8
```

Do not commit extracted proprietary documentation unless you have explicit permission.

## Local Manual Workflow

For syntax-sensitive tasks, the skill first looks for:

```text
references/sprocess-user-guide/INDEX.md
```

If the extracted chunks are present, Codex searches them before choosing unfamiliar SProcess syntax. If they are missing, the assistant should ask whether you already have extracted chunks, whether you want to extract a licensed local PDF, or whether you want to continue in draft mode and validate later against your installed Sentaurus release.

If you choose PDF extraction, provide the local PDF path. The default output directory is `references/sprocess-user-guide/`, which is ignored by git.

Draft mode is based only on this skill's public instructions, synthetic examples, lightweight command index, and the model's general knowledge. It is suitable for conceptual planning and initial skeletons, but not for claiming compatibility with a specific Sentaurus release.

The extracted manual directory is ignored by git by default.

## Public Repository Safety

Before publishing:

- Confirm `references/sprocess-user-guide/` is not committed.
- Confirm official training PDFs, HTML pages, tutorial decks, and proprietary process recipes are not committed.
- Run a secret scan for tokens, API keys, local usernames, absolute paths, and license-server details.
- Keep examples synthetic, minimal, and authored for this repository.
- Use local licensed documentation only on your machine.

Useful local checks:

```powershell
rg -n -i "api[_-]?key|secret|token|password|bearer|authorization|license|lm_license|[A-Z]:\\\\|/Users/" .
git status --ignored
```

Validate helper scripts still run before pushing:

```powershell
python -m py_compile scripts\render_sprocess_cross_section.py scripts\extract_pdf_reference.py
python scripts\render_sprocess_cross_section.py references\examples\minimal_oxidation_implant.cmd --analysis-out references\examples\minimal_oxidation_implant_analysis.md
```

If you later discover that secrets, private paths, or licensed material slipped in, remove them from the public branch, rotate any exposed credentials, and rewrite git history before sharing the repository more widely.

## Copyright And Trademarks

This repository's original code and skill text are released under the MIT License. Third-party product names, including Synopsys and Sentaurus, are trademarks of their respective owners.

No Synopsys software, manuals, licensed examples, or proprietary process data are included in the public release. Users are responsible for complying with their own software and documentation license agreements.
