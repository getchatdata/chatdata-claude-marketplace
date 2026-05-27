---
description: Connect your token, attach the private company repo, and start shared context sync.
---

# Login

Use this once per user or machine to connect Claude Code to the ChatData portal.

Preferred secure form when the user is running the command themselves:

```bash
read -r -s CHATDATA_TOKEN
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" login \
  --email "<user@company.com>" \
  --token-env CHATDATA_TOKEN
unset CHATDATA_TOKEN
```

When Claude Code is executing for the user, do not ask the user to paste the token into the transcript. Ask them to copy the token to the local clipboard, then run:

```bash
CHATDATA_TOKEN="$(pbpaste)" \
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" login \
  --email "<user@company.com>" \
  --token-env CHATDATA_TOKEN
```

Non-interactive form, only when the token is already in a safe environment variable:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" login \
  --email "<user@company.com>" \
  --token-env CHATDATA_TOKEN
```

Avoid putting the token directly in the command line, plan text, shell history, screenshots, or transcripts.

After this succeeds, ChatData stores the email, token, company domain, and company repo manifest locally. Future sessions should not ask for GitHub setup again unless the portal config changes or the local state is deleted.

Default behavior:

- derive company key from the work email domain
- fetch repo config from `https://getchatdata.com/api/portal/config`
- create or attach the local company repo scaffold
- write `.chatdata/company-repo.json`
- write `~/.chatdata/company-domain-map.json`
- use backend-managed sync for ChatData-managed repos, so local GitHub credentials are not required

Do not ask for company name. The domain is the company key.
