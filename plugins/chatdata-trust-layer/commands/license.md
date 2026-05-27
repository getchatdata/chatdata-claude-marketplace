---
description: ChatData command for ChatData License.
---

# ChatData License

Use this command to activate a manual ChatData license key after the 7-day trial.

If the user provides a license key, run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" license --key "$ARGUMENTS"
```

If no key is provided, explain that v1 uses manual license keys and that value commands stop after the 7-day trial until a key is activated.

For internal support only, a key can be issued with:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" license --issue --email person@company.com --expires 2026-12-31
```

Do not present this as a hardened billing system. It is the v1 trial gate until Stripe is added.
