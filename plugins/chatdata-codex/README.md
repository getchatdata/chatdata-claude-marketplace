# ChatData For Codex

ChatData for Codex is the Codex adapter for the same ChatData trust layer used by the Claude Code plugin.

The product core is shared:

- private `ChatData-<Company>` context repo
- domain-to-repo mapping
- metric packets
- approved answer paths
- corrections
- proof receipts
- validation and eval workflows
- 7-day trial and manual license state

This adapter exists so ChatData is not locked to one agent surface. Claude Code remains the first marketplace path, but Codex can run the same principal data workflow from the shared company repo.

The Codex package is self-contained for installation. It carries the shared ChatData helper, the template company repo assets, and the synthetic benchmark fixture used for first-session proof.

## Local Use

The Codex adapter calls the bundled helper in:

```bash
plugins/chatdata-codex/bin/chatdata_state.py
```

Core status smoke test:

```bash
python3 plugins/chatdata-codex/bin/chatdata_state.py status
```

Install from this repo as a local Codex marketplace:

```bash
codex plugin marketplace add <path-to-this-repo>
codex plugin add chatdata-codex@chatdata
```

Install from the public ChatData Codex marketplace:

```bash
codex plugin marketplace add getchatdata/chatdata-codex-marketplace
codex plugin add chatdata-codex@chatdata
```

## Boundary

Do not fork product logic here. Keep durable ChatData behavior in the shared helper and sync this package from `plugins/chatdata-trust-layer/` before releases.
