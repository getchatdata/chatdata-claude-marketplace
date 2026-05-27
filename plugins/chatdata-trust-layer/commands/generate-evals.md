---
description: ChatData command for Generate Evals.
---

# Generate Evals

Use this command to create recurring KPI eval questions for the active pilot domain.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

Requirements:

1. Generate questions the business actually asks in weekly review.
2. Tie each question to an expected route, metric, caveat, and accepted answer states.
3. Distinguish reviewed high-value paths from exploratory ones.
4. Prefer breadth of recurring phrasing over generic warehouse chat prompts.

Target:

- at least 30 recurring questions
- enough variation to catch routing drift
