---
description: ChatData command for Benchmark.
---

# Benchmark

Use this command to show the local synthetic ChatData workflow benchmark.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

Then run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" benchmark
```

This benchmark is a local product smoke test. Do not market it as public performance data unless a reproducible public benchmark suite exists.
