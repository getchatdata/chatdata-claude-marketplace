---
description: Sync reusable context through the ChatData MCP and report the exact shared-state status.
---

# Sync Context

Use this command to sync shared context through the ChatData MCP. The plugin is the workflow harness; the MCP is the shared context transport.

First use the ChatData MCP server and run `chatdata_doctor`.

- If the tool is unavailable, stop and say: "ChatData MCP is not connected. Install or repair the MCP from ChatData Settings, then rerun `/chatdata:sync-context`."
- If `chatdata_doctor` reports config, consent, or hub errors, stop and show the exact failing check plus the next install/repair command.
- If healthy, continue.

Then use the ChatData MCP server and run `chatdata_pull_context` so this session starts from the latest approved shared context.

For local artifacts created or changed in this workflow, write them back through MCP tools:

- metric packet -> `chatdata_create_metric_card`
- reviewed recurring question or answer path -> `chatdata_save_answer_path`
- proof receipt -> `chatdata_create_proof_receipt`
- any other Markdown context file -> `chatdata_propose_patch`, then `chatdata_publish_patch` only after review/approval is clear

Only after the MCP write path is unavailable should you inspect the legacy local helper for diagnostic detail:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" github
```

Legacy helper behavior:

- read `.chatdata/company-repo.json`
- use the portal-provided remote URL when available
- initialize the local company repo as a Git repo if needed
- attach or update `origin`
- commit local context changes
- push to the private repo
- report `synced` or the exact blocker

Do not treat a local Git push as the product sync path for managed ChatData work. It is a transparent fallback/debug path.

If the user wants a repo creation plan, run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" github --create-plan
```

Interpret legacy sync modes:

- `chatdata-managed`: the plugin should call ChatData backend sync. GitHub credentials stay on ChatData infrastructure.
- `customer-github-app`: a customer admin installed the ChatData GitHub App once. ChatData mints short-lived server-side tokens.
- `local-git`: the customer uses local Git or `gh` auth. This is transparent but less magical.

Do not put GitHub private keys in the plugin. Do not run repo creation, push, or access-grant commands without explicit approval.

After every useful company analysis or reusable context write, run this command as its own final step. If MCP-backed shared sync is unavailable, block stakeholder-facing company workflow and explain the missing setup piece. Local-only trial work can continue only when the user explicitly accepts that it will not update team context.

Required output:

- MCP status: connected, unhealthy, or missing
- context pull revision or exact pull blocker
- artifacts written through MCP, grouped by tool name
- any local-only fallback used
- final shared context status: synced, blocked, or local-only
