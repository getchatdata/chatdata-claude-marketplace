---
description: Commit and push reusable context to the private company repo.
---

# Sync Context

Use this command to sync shared context to the company repo.

Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" github
```

Default behavior:

- read `.chatdata/company-repo.json`
- use the portal-provided remote URL when available
- initialize the local company repo as a Git repo if needed
- attach or update `origin`
- commit local context changes
- push to the private repo
- report `synced` or the exact blocker

If the user wants a repo creation plan, run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" github --create-plan
```

Interpret sync modes:

- `chatdata-managed`: the plugin should call ChatData backend sync. GitHub credentials stay on ChatData infrastructure.
- `customer-github-app`: a customer admin installed the ChatData GitHub App once. ChatData mints short-lived server-side tokens.
- `local-git`: the customer uses local Git or `gh` auth. This is transparent but less magical.

Do not put GitHub private keys in the plugin. Do not run repo creation, push, or access-grant commands without explicit approval.

After every useful company analysis or reusable context write, run this command as its own final step. If shared sync is unavailable, block stakeholder-facing company workflow and explain the missing setup piece. Local-only trial work can continue only when the user explicitly accepts that it will not update team context.
