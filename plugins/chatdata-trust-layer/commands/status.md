---
description: Show trial, repo, metrics, proof, onboarding progress, and setup health.
---

# ChatData Status

Show the current ChatData trial/license status, local setup health, company context repo status, trusted metrics, proof receipts, and estimated value created.

Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" status
```

Relay the output directly. If guided onboarding is incomplete, move the next incomplete component forward. If the trial expired, tell the user that `/chatdata:license` activates a manual key and `/chatdata:proof` can still export their proof pack.
