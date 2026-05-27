---
description: ChatData command for Scan Sources.
---

# Scan Sources

Use this command to inspect the local trust-layer repo plus the customer's dbt artifacts, dashboard exports, and owner mapping.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

Checklist:

1. Identify the top recurring metrics already named in dashboards or docs.
2. List trusted dashboard links, benchmark SQL candidates, and owner gaps.
3. Call out weak or missing metadata without blocking the whole install.
4. Leave the user with a short source-readiness summary for the top-10-metric wedge.

Prefer concrete files, folders, and missing fields over strategy prose.
