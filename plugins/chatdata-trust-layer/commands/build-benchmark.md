---
description: ChatData command for Build Benchmark.
---

# Build Benchmark

Use this command when a trusted SQL path or dashboard benchmark is missing for a metric.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

Sequence:

1. Look for an existing benchmark query under `queries/trusted/`.
2. If absent, draft a candidate benchmark query under `queries/generated/`.
3. Link the benchmark back to the metric packet and answer path.
4. Record what still needs analyst review before the path can be promoted beyond draft.

Do not present generated SQL as trusted until it has a visible review path.
