# ChatData Trust Layer Repo

Customer-owned trust-layer repo for both ChatData product surfaces:

- ChatData for Claude Code as the principal analyst workbench
- ChatData for Slack as the organizational distribution surface

This repo is the canonical source of truth for:

- metric packets
- answer paths
- trusted benchmark SQL
- trusted artifact metadata
- eval questions
- operating briefs and WBR prep inputs
- published Slack bundles

The Slack runtime should read only the immutable files under `published/`.

The publish step copies canonical content into `published/` and writes `slack_context.json` with the full runtime bundle payload.
