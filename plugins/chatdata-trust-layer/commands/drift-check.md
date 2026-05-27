---
description: ChatData command for Drift Check.
---

# Drift Check

Use this command after dbt changes, dashboard edits, or repeated Slack feedback incidents.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

Tasks:

1. Compare changed files with the current metric packets and answer paths.
2. Flag any reviewed or auto-trusted paths that may need downgrade or quarantine.
3. Suggest the smallest repair set that restores trust.
4. Update the review-readiness summary when drift is confirmed.
