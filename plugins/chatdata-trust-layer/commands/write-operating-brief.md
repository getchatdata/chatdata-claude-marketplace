---
description: Turn trusted context into a concise decision memo with caveats and next steps.
---

# Write Operating Brief

Use this command when the user wants a principal-level operating brief from trusted ChatData context.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

Preferred flow:

1. Confirm the trust-layer repo path and the time window.
2. Review recent metric packets, trusted artifacts, answer paths, and drift or feedback incidents.
3. Write a short operating brief in plain language with:
   - what changed
   - what matters
   - what is noisy or still uncertain
   - what decision or follow-up should happen next
4. Run `/chatdata:sync-context` as its own final step after writing any operating brief, decision note, correction, answer path, or proof receipt.

Required output:

- title
- 3 to 5 key findings
- trust and caveat notes
- recommended next steps
- context sync status
