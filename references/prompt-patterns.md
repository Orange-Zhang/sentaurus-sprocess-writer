# Prompt Patterns

Use these patterns to ask for missing process information without overloading the user.

## New deck

Ask for:

- target device/process
- 1D/2D/3D intent
- substrate material, orientation, and doping
- sequence of deposition, etch, implant, anneal, oxidation, or diffusion steps
- expected final `.tdr` name

## Modify existing deck

Ask for:

- file to edit
- desired process change
- whether output filenames should change
- whether downstream SDevice decks depend on region/contact names

## Manual-driven syntax check

Ask for:

- command or feature to verify
- whether `references/sprocess-user-guide/` already contains extracted chunks
- local manual PDF path if chunks are not extracted yet
- installed Sentaurus release if syntax may be version-specific

Suggested prompt:

```text
I need to verify SProcess syntax for this change. Do you already have extracted manual chunks under `references/sprocess-user-guide/`, or should I extract a licensed local PDF with `scripts/extract_pdf_reference.py`? If neither is available, I can continue in draft mode and mark the deck for validation in your installed Sentaurus release.
```
