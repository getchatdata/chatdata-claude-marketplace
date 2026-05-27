---
description: Make ChatData own this Claude Code workspace footer, agent metadata, and attribution.
---

# Activate Session

Use this when Claude Code has loaded ChatData commands but the footer or metadata still shows another global agent.

Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" activate-session
```

Default behavior:

- writes project-local `.claude/settings.local.json`
- preserves existing local permissions
- sets the session agent to `chatdata:code`
- replaces the status line with the ChatData trial, repo, sync, metric, proof, and onboarding summary
- sets ChatData attribution for this workspace

This is project scoped. It does not edit the user's global `~/.claude/settings.json`.

After it succeeds, restart Claude Code from the same workspace:

```bash
claude --plugin-dir "${CLAUDE_PLUGIN_ROOT}"
```
