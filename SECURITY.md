# Security Policy

## Supported Scope

This project is a local Codex skill plus helper scripts. It should not store credentials, license-server details, private TCAD decks, or proprietary documentation in public git history.

## Before Publishing

Run at least these checks:

```powershell
rg -n -i "api[_-]?key|secret|token|password|bearer|authorization|license|lm_license|[A-Z]:\\\\|/Users/" .
git status --ignored
```

Review ignored files before first push. The `.gitignore` is intentionally conservative because local Sentaurus manuals, official examples, generated manual chunks, and private process decks may be license restricted.

## Reporting

If you find accidentally published secrets, private paths, or licensed content, remove the material from the public branch immediately and rotate any affected credentials. If the data entered git history, rewrite the history before sharing the repository more widely.
