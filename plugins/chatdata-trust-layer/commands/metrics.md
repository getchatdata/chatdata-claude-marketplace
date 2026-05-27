---
description: Create or inspect metric trust packets with definitions, sources, caveats, and owners.
---

# Metrics

Use this command to create or inspect ChatData metric trust packets.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

If this is company work, also require the shared context repo:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" company-repo --require
```

For a new metric, run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" metrics "<metric name>"
```

Then complete the packet with:

- official definition
- formula
- numerator and denominator
- grain and timezone
- required filters and exclusions
- blessed source path
- freshness rule
- caveats
- validation tolerance
- business owner and data owner
- approved answer paths

If the metric is ambiguous, ask for the smallest missing detail instead of guessing.

After creating or updating a packet in a company repo, run `/chatdata:sync-context` as its own final step and report the sync status.
