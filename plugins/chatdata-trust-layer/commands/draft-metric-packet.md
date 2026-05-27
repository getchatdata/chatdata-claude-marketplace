---
description: ChatData command for Draft Metric Packet.
---

# Draft Metric Packet

Use this command when one metric needs to move from loose tribal knowledge into a concrete trust packet.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

Workflow:

1. Start from the canonical metric template in `metrics/`.
2. Pull the best available definition from dashboard labels, dbt docs, trusted SQL, and owner notes.
3. Fill owners, grain, timezone, caveats, freshness, clarification rules, and escalation rules.
4. Keep uncertain fields explicit instead of inventing confidence.
5. Save the packet as a draft and list the open review questions.

Required output:

- metric packet path
- fields completed
- fields still missing
- benchmark path recommendation
