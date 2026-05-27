---
name: company-context-repo
description: Enforce ChatData's shared private company context repo for team or company analytics work.
---

# Company Context Repo

Use this skill whenever the user mentions a company, team rollout, shared data context, GitHub repo, catalog, Slack rollout, WBR, recurring metrics, or work that multiple people will reuse.

ChatData's default stance: serious data analysis should not stay single-player. Company work needs a shared private context repo, usually named `ChatData-<Company>`, that everyone on the company analytics workflow can read and improve.

## Enforcement

Before company or team analysis:

1. Run the trial/license guard.
2. Run the company repo check:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" company-repo --require
```

If the repo is configured, continue without ceremony.

If the repo is missing, stop the analysis and run `/chatdata:company-repo` setup. For managed onboarding, ChatData creates the private GitHub repo and grants the customer's GitHub users or team access. For self-serve onboarding, the customer can create it in their GitHub org and provide the owner, repo, local path, and remote.

Do not create a private GitHub repo, push code, invite users, or change access without explicit approval and working GitHub auth.

## Read Before Work

Before raw discovery, inspect the company repo:

- `metrics/`
- `answer-paths/`
- `corrections/`
- `sources/`
- `decisions/`
- `playbooks/`
- `evals/`

Use this shared context ahead of private chat history, one-off notebooks, or guessed metric definitions.

## Write Back

After useful work, propose updates to the shared repo:

- metric packet for a new or corrected metric
- answer path for a recurring question
- correction file for a mistake, caveat, rejected definition, or gotcha
- proof receipt for material work
- decision note for WBR or executive-review output
- eval case for a question that should not regress

Prefer a visible diff or pull request for changes that affect other users. Do not silently overwrite reviewed context.

## Sync After Work

After every useful analysis or reusable context write, run sync as its own step:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" github
```

Treat `Context sync: synced` as the successful end state. If sync is blocked, report the exact blocker before presenting the work as team-ready.

## Output Rule

Tell the user where reusable context was read from, what was written back, and whether context sync succeeded. Keep customer-facing output ChatData-branded.
