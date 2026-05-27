---
description: Prepare a WBR from trusted metrics, answer paths, caveats, and follow-ups.
---

# Prepare WBR

Use this command when a founder, operator, or data lead wants the weekly business review prepared from the trust-layer repo.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

Preferred flow:

1. Confirm the trust-layer repo path and the reporting period.
2. Review the top metrics, published answer paths, trusted artifacts, and any known caveats.
3. Draft a compact WBR prep note with:
   - biggest metric movements
   - drivers already supported by trusted evidence
   - unresolved questions that still need review
   - follow-ups to assign before the meeting
4. Run `/chatdata:sync-context` as its own final step after writing any decision note, proof receipt, correction, answer path, or WBR artifact.

Required output:

- WBR headline summary
- metric movement bullets
- unresolved risks
- recommended follow-up owners
- context sync status
