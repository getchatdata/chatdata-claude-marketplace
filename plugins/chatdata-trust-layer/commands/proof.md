---
description: Record or export proof receipts with sources, checks, confidence, time, and value.
---

# Proof

Use this command to record or export ChatData proof receipts.

Proof export is allowed even if the trial has expired.

To show the proof pack, run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" proof
```

To record a receipt after a useful workflow, run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" proof --record \
  --workflow "<workflow>" \
  --question "<question>" \
  --artifact "<artifact path>" \
  --sources "<comma-separated sources>" \
  --validation "<comma-separated validation checks>" \
  --confidence "<high|medium|low>" \
  --time-saved-minutes "<minutes>" \
  --value-usd "<estimated value>" \
  --next-action "<next action>"
```

Only estimate time or value when the assumptions are visible. Label estimates as estimates.

When a company context repo is configured, the helper also appends the proof receipt to `proof/impact-log.jsonl` in the shared repo so the work compounds for the team.

After recording a company proof receipt, run `/chatdata:sync-context` as its own final step and report the sync status.
