---
description: Show the next setup component so the first analysis has source, metric, proof, and sync.
---

# Onboarding

Show the guided first-session checklist and the next missing component.

Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" onboarding
```

Use this on the first ChatData session, after `/chatdata:login`, or whenever the user seems blocked on what to do next.

The checklist is component-based:

- role, owned metrics, and recurring forum
- multiplayer company context repo
- first data source
- one metric trust packet
- first proof receipt

If the local synthetic retail dataset is available, ChatData should offer it as a low-friction first data component. In real customer work, replace that with the user's own CSV, warehouse, dbt repo, BI export, MCP source, or dashboard source path.

Do not ask for every setup detail at once. Move the next incomplete component forward, then run a tiny proof workflow.
