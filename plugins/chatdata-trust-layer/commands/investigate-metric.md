---
description: ChatData command for Investigate Metric.
---

# Investigate Metric

Use this command when one operator wants a principal-level read on a KPI movement or recurring business question inside Claude Code.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

Preferred flow:

1. Confirm the trust-layer repo path, reporting period, and metric or KPI in question.
2. Read the metric packet, trusted artifacts, and any matching answer paths first.
3. Produce a concise investigation with:
   - direct answer
   - trust state
   - evidence used
   - caveats
   - recommended next step
4. If the answer depends on missing benchmark coverage or an unreviewed path, say so clearly and recommend the builder command that should close the gap.
5. Run `/chatdata:sync-context` as its own final step after any proof, metric packet, correction, answer-path, or decision write.

Required output:

- one-sentence answer
- evidence list
- trust label
- caveats
- next command or follow-up
- context sync status
