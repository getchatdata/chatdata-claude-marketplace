---
description: ChatData command for Settings.
---

# Settings

Use this command to show or update ChatData local settings.

Show settings:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" settings
```

Update settings:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" settings --set telemetry=false --set status_line=true
```

Default posture:

- local-first on
- telemetry off
- proof receipts on
- status display on

Never enable telemetry without explicit user opt-in.
