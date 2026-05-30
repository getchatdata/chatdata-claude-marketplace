# Changelog

## 0.3.4 - 2026-05-30

- added `/chatdata:publish-patch` so pending MCP patches have a real Claude command path instead of a nonexistent instruction
- taught the command to list pending patches through `chatdata_list_review_queue`, require an explicit patch id, and publish with `chatdata_publish_patch`

## 0.3.3 - 2026-05-30

- made ChatData for Claude Code a plugin-plus-MCP install: the plugin owns workflow enforcement, while the MCP owns shared context transport, status, and workspace-backed reads/writes
- updated `/chatdata:sync-context` to require `chatdata_doctor`, pull hub context through `chatdata_pull_context`, and write reusable artifacts through MCP tools before falling back to local-only state
- updated `/chatdata:audit-context` to audit the MCP context view first, including pull/export/conflict checks, and block company workflows when the MCP is missing
- updated the default principal agent to require MCP-backed sync after useful analysis, validation, WBR prep, proof, corrections, metric packets, answer paths, decisions, or eval writes

## 0.3.2 - 2026-05-27

- switched ChatData-managed company repo sync to the ChatData backend so Claude Code users do not need local GitHub write access
- added secure login token input through environment variables or stdin to keep portal tokens out of command history and plan text
- updated Claude marketplace metadata for getchatdata-owned distribution

## 0.3.1

- added `/chatdata:activate-session` and a ChatData statusline so project-local Claude Code sessions can show `chatdata:code` instead of a globally configured agent
- made the statusline lead with the product outcome: AI analytics slop loops blocked, saved time, estimated cost avoided, trusted metric count, sync state, and trial status
- added `chatdata:code` as the cleaner default visible agent id while keeping the older principal workflow files available

## 0.3.0 - 2026-05-26

- made the private company context repo a first-class ChatData primitive
- added `/chatdata:company-repo`, `/chatdata:sync-context`, `/chatdata:audit-context`, and `/chatdata:create-evals`
- added domain mapping so later users from the same email domain attach to the existing company repo
- required company repo setup for company investigation and validation workflows
- wrote metric packets and proof receipts to the shared company repo when configured
- added GitHub readiness checks without storing GitHub private keys in the plugin

## 0.2.0 - 2026-05-25

- repositioned ChatData for Claude Code around the B2C principal data professional workflow
- added 7-day local trial state, manual license activation, settings, proof receipts, status, benchmark, data-source, and metric-packet helpers
- added plugin-native skills for framing, trust packets, routing, data-quality preflight, SQL loops, parallel investigation, validation, action follow-through, feedback memory, proof receipts, and privacy/trial behavior
- added `chatdata:principal` as the default agent and kept `principal-analyst` as a legacy alias
- gated value commands behind trial/license state while keeping status, license, and proof export available

## 0.1.0 - 2026-04-14

- packaged ChatData for Claude Code as one plugin with principal analyst mode and builder mode
- added principal workflows for metric investigation, WBR prep, and operating brief generation
- kept trust-layer bootstrap, benchmark, eval, drift, and Slack bundle publish flows in the same package
