---
description: Apply on first run, setup, install, data connection, or when ChatData profile context is missing.
---

# ChatData Context Bootstrap

Set up only the context needed for the user's first useful workflow.

Capture:

- role or job-to-be-done
- business context
- 3-5 owned metrics
- data sources available now
- recurring decision forum
- preferred output format

Use `python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" start` to initialize local state. Auto-detect project context when possible. Ask once, not file by file.

Do not overwrite existing local user configuration. Merge or append.
