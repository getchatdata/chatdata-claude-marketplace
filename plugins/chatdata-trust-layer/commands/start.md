---
description: Start the trial, create local state, and launch the first proof workflow.
---

# Start ChatData

Use this command to begin the 7-day ChatData trial and create local state for the current project.

Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" start
```

If this is the first time ChatData is loaded in this workspace, also run `/chatdata:activate-session` so the ChatData status line, agent metadata, and attribution take over the project footer. The status line is opt-in per workspace and only appears after activation.

If the user has portal access, sync the company repo during start:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" start \
  --email "<user@company.com>" \
  --token "<chatdata-token>"
```

Then ask one concise setup question if profile context is still missing:

- role or job-to-be-done
- 3-5 metrics they are responsible for
- one recurring forum or stakeholder workflow
- preferred output format

The helper prints the guided onboarding checklist automatically. Treat that checklist as the first-session path, not as background copy.

After setup, run a tiny first proof workflow:

1. If this is company or team work, run `/chatdata:login` or `/chatdata:company-repo --email <user@company.com>` to auto-attach the shared private context repo.
2. Create or identify one metric trust packet.
3. Run a quick trusted-context read.
4. Produce the first proof receipt with `/chatdata:proof`.
5. Run `/chatdata:sync-context` as its own final step so the shared company context is current.

Keep the output ChatData-branded. Do not mention internal inspiration sources.
