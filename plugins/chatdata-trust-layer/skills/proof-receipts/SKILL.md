---
description: Apply after a useful ChatData workflow creates a decision artifact, validated analysis, metric packet, WBR prep, or reusable answer path.
---

# Proof Receipts

At the end of useful work, record a proof receipt when appropriate:

- workflow
- question
- artifact path
- sources used
- validation checks
- confidence
- estimated time saved
- estimated value created
- next action

Use the exact supported CLI flags:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" proof --record \
  --workflow "<workflow>" \
  --question "<question>" \
  --artifact "<artifact path>" \
  --sources "<comma-separated sources>" \
  --validation "<comma-separated validation checks>" \
  --confidence "<high|medium|low>" \
  --time-saved-minutes "<minutes>" \
  --value-usd "<estimated dollar value>" \
  --next-action "<next action>"
```

Do not invent unsupported flags such as `--value-created`. If the value is qualitative, put it in `--next-action` or omit `--value-usd`.

Only estimate time or value when the assumption is visible. These receipts power trial retention and the user's promotion evidence.

After recording a proof receipt for company work, run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" github
```

Report whether the receipt synced to the shared company context repo.
