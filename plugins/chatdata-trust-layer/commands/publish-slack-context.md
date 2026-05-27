---
description: ChatData command for Publish Slack Context.
---

# Publish Slack Context

Use this command when canonical trust-layer files are ready to turn into an immutable runtime bundle for the Slack app.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/publish_bundle.py" <trust-layer-repo>
```

After publish:

1. Report the manifest path, bundle version, and content hash.
2. List metric and answer-path counts.
3. Call out any draft-only metrics that still cannot be promoted.
