---
description: Create, attach, or enforce the shared private repo that makes analysis multiplayer.
---

# Company Repo

Use this command to create or attach the shared private GitHub-backed ChatData context repo for a company.

This repo is required for company or team analysis. If it is already configured, do not ask again. Read it, use it, and write useful context back to it.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

For a new company, create or attach the repo:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" company-repo \
  --company "<Company>" \
  --domain "<company.com>" \
  --owner "<github-owner>" \
  --repo "ChatData-<Company>" \
  --path "<local clone path>" \
  --remote "git@github.com:<github-owner>/ChatData-<Company>.git" \
  --sync-mode "chatdata-managed"
```

For another user at the same company, attach from their email domain:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" company-repo --email "<user@company.com>"
```

The managed v1 model maps `@company.com` to one private repo. Paras can create the repo manually during onboarding, then ChatData stores the domain mapping so later users from the same domain attach without a new setup conversation.

If ChatData is doing managed onboarding, create the private GitHub repo first, then grant the customer's GitHub users or team access:

```bash
gh repo create <github-owner>/ChatData-<Company> --private \
  --description "ChatData shared context repo for <Company>"
```

Do not run `gh repo create`, `git push`, or access grants without explicit approval from the repo owner. Claude Code will show shell commands and may ask permission depending on the user's settings. GitHub auth comes from the user's local `gh` session or SSH keys.

Do not put ChatData GitHub private keys inside this plugin. For magical sync, use ChatData-managed backend sync or a GitHub App server-side. The plugin should hold only a ChatData license/session token and the domain-to-repo mapping.

Before any company analysis, enforce:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" company-repo --require
```

Use the repo as the multiplayer source of truth:

- read `metrics/`, `answer-paths/`, `corrections/`, `sources/`, `decisions/`, `playbooks/`, and `evals/` before raw discovery
- create or update metric packets in the shared repo, not only local `.chatdata`
- append proof receipts to `proof/impact-log.jsonl`
- propose shared repo changes through a diff or pull request when multiple people depend on the context
- never leave reusable metric definitions, caveats, or approved answer paths only in chat
