---
description: ChatData command for Create Evals.
---

# Create Evals

Use this command to create reliability tests for the shared company context.

First run the company repo guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard --company-repo
```

Create eval cases under the company repo's `evals/` folder.

Minimum coverage:

- one real-user prompt per trusted metric
- one ambiguity test per overloaded business term
- one time-scope test for last week, last 30 days, current month, and partial periods
- one rejected-metric test for each known bad definition
- one source tie-out test for every WBR or executive-review metric
- one data-quality test for nulls, duplicates, impossible values, and missing segments where relevant

Each eval should include:

- natural-language prompt that does not leak table or column names
- expected metric or answer path
- expected validation checks
- source-of-truth SQL, dashboard, or artifact
- pass criteria
- owner

After writing evals, show the diff and recommend `/chatdata:audit-context` before using them as a release gate.
