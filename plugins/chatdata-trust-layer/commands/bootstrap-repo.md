---
description: ChatData command for Bootstrap Repo.
---

# Bootstrap Repo

Use this command when the customer analytics engineer is ready to create the ChatData trust-layer repo for the pilot domain.

1. Run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

2. Confirm the target directory for the customer-owned repo.
3. Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/bootstrap_repo.py" <target-dir>
```

4. Open the new repo and fill the owner mapping, dashboard URLs, and top-10-metric list.
5. End by summarizing what still needs customer input before the first publish.

Required output:

- repo path
- copied template structure
- missing inputs list
- recommended next command
