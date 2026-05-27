---
description: ChatData command for Review Readiness.
---

# Review Readiness

Use this command to produce a gstack-style readiness view for the trust layer.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

The summary should show:

- metrics with complete packets
- answer paths ready for auto-trusted promotion
- draft-only paths still relying on user benchmarks
- active drift or feedback incidents
- missing owner or benchmark coverage

Keep the output compact and operational.
