# ChatData For Claude Code

ChatData for Claude Code helps data professionals operate like principal data professionals inside Claude Code.

This package is the Claude Code workflow adapter for the shared ChatData trust layer. The ChatData MCP server is the context transport and workspace API. Customers should install both: the plugin gives Claude Code the reliable analytics workflow, and the MCP keeps shared context, proof, metric packets, answer paths, and review state in sync with ChatData.

It packages the working habits that strong data leaders expect by default:

- clarify the decision before analysis
- use governed metric definitions and trusted source paths first
- check data quality before presenting numbers
- validate conclusions before sharing them
- attach caveats, confidence, owner, and next action to material findings
- capture corrections and proof receipts so future work compounds
- make analysis multiplayer by storing reusable context in a shared private company repo

Created by Paras Doshi. ChatData is a white-labeled product; customer-facing files, commands, and outputs should read as ChatData-originated.

## Trial And Pricing

- 7-day free trial
- `$49/month` after the trial
- no Stripe checkout in v1
- manual license activation with `/chatdata:license`
- expired trials block value commands but still allow `/chatdata:status`, `/chatdata:license`, and `/chatdata:proof`

Local state lives in:

- `~/.chatdata/license.json`
- `~/.chatdata/profile.json`
- `~/.chatdata/settings.json`
- project `.chatdata/metrics/*.yaml`
- project `.chatdata/impact-log.jsonl`
- project `.chatdata/corrections/*.yaml`
- project `.chatdata/company-repo.json`

## Plugin Plus MCP Contract

ChatData uses two harnesses together:

1. `ChatData for Claude Code` plugin
   - enforces the principal workflow
   - routes vague questions
   - requires proof, caveats, validation, and follow-up state
   - runs `/chatdata:sync-context` after useful analysis or reusable context writes
   - stops and guides setup when the MCP is missing
2. `ChatData MCP`
   - verifies workspace auth and consent with `chatdata_doctor`
   - pulls approved shared context with `chatdata_pull_context`
   - writes reusable artifacts with `chatdata_create_metric_card`, `chatdata_save_answer_path`, `chatdata_create_proof_receipt`, or `chatdata_propose_patch`
   - exposes conflict, member, diff, rollback, and export tools for shared trust-layer operations

The plugin should not treat local GitHub sync as the primary path for company context. Local files and Git are useful for transparency and debugging, but MCP-backed context is the product path.

When a command needs shared context, first use the ChatData MCP server and run `chatdata_doctor`. If the tool is unavailable or unhealthy, stop company/stakeholder workflow and guide the user to install or repair the MCP. Local-only trial work can continue only when the user explicitly accepts that it will not update team context.

## Multiplayer Company Context

ChatData should not leave serious data work in one person's chat history.

For company or team use, the plugin requires MCP-backed shared context. A readable private context repo can still exist, normally named `ChatData-<Company>`, but the MCP is the authoritative sync path for managed onboarding. ChatData can create or maintain the private context world during managed onboarding. Self-serve teams can still attach a customer-owned repo when that deployment mode is explicitly approved.

The repo stores the shared artifacts that make AI analysis compound:

- `metrics/`
- `answer-paths/`
- `corrections/`
- `proof/`
- `decisions/`
- `sources/`
- `playbooks/`
- `evals/`

For company work, `/chatdata:investigate` and `/chatdata:validate` require healthy ChatData MCP context before they proceed. If the MCP is connected, ChatData uses it without asking. If it is missing, ChatData stops and guides MCP setup first.

ChatData-managed context syncs through the ChatData backend, so the user's local GitHub account does not need write access to a private repo. Customer-owned and local-git modes can still use the customer's own GitHub auth when that is the approved deployment model.

## Default Agent

The plugin ships `chatdata:code` as its default agent through `settings.json`.

That agent enforces the principal workflow:

1. route the question by complexity
2. frame non-trivial work around decision, metric, grain, source, timeframe, edge cases, and success criteria
3. read metric packets, answer paths, trusted SQL, corrections, and catalog context first
4. run data-quality preflight
5. use a self-correcting SQL loop when querying
6. investigate bad-data or metric-movement cases in parallel
7. validate with structural, logical, business-rule, source tie-out, and Simpson's Paradox checks
8. return answer, implication, evidence, caveats, confidence, owner, next action, and follow-up date
9. record proof receipts when useful work is completed

## Commands

### Trial, License, And Proof

- `/chatdata:start`
- `/chatdata:onboarding`
- `/chatdata:activate-session`
- `/chatdata:login`
- `/chatdata:status`
- `/chatdata:impact`
- `/chatdata:license`
- `/chatdata:settings`
- `/chatdata:company-repo`
- `/chatdata:sync-context`
- `/chatdata:proof`
- `/chatdata:benchmark`

### Principal Workflow

- `/chatdata:connect-data`
- `/chatdata:metrics`
- `/chatdata:investigate`
- `/chatdata:validate`
- `/chatdata:audit-context`
- `/chatdata:create-evals`
- `/chatdata:investigate-metric`
- `/chatdata:prepare-wbr`
- `/chatdata:write-operating-brief`

### Trust Layer Builder Workflow

- `/chatdata:bootstrap-repo`
- `/chatdata:scan-sources`
- `/chatdata:draft-metric-packet`
- `/chatdata:build-benchmark`
- `/chatdata:generate-evals`
- `/chatdata:drift-check`
- `/chatdata:publish-slack-context`
- `/chatdata:review-readiness`

The plugin is one product surface. The personal Claude Code wedge and the future Slack/team rollout use the same trust layer.

## Install

Install from the approved Claude Code distribution once the listing is live. During private beta, use the invite instructions provided in the ChatData portal.

The install is not complete until both checks pass:

```bash
claude plugin list
claude mcp get chatdata
```

`claude plugin list` should show `chatdata@chatdata` enabled. `claude mcp get chatdata` should show `Status: Connected`, `Command: node`, and the ChatData MCP `packages/mcp/dist/index.js` path.

Do not put portal tokens in shell history. Use the portal's **Copy terminal setup command** or `/chatdata:login` with the secure token environment flow documented in the command.

## Helper Scripts

- `bin/chatdata_state.py` manages trial/license state, settings, company repo setup, proof receipts, local data-source manifests, metric packet creation, and synthetic benchmark output.
- `bin/bootstrap_repo.py <target-dir>` copies the template repo into a customer-owned path.
- `bin/publish_bundle.py <repo-path>` renders an immutable published bundle from canonical files.

Examples:

```bash
python3 bin/chatdata_state.py start
python3 bin/chatdata_state.py status
python3 bin/chatdata_state.py license --key CHATDATA-YYYYMMDD-EMAILHASH-CHECKSUM
python3 bin/chatdata_state.py company-repo --company Foo --owner your-github-org --repo ChatData-Foo
python3 bin/chatdata_state.py proof
python3 bin/bootstrap_repo.py /tmp/customer-chatdata-trust
python3 bin/publish_bundle.py /tmp/customer-chatdata-trust
```

To publish directly to the Slack runtime once the Worker is deployed:

```bash
python3 bin/publish_bundle.py <repo-path> \
  --runtime-url https://api.getchatdata.com \
  --admin-token "$CHATDATA_ADMIN_TOKEN"
```

## Template Repo

The template copied by `bootstrap_repo.py` lives under `./assets/template-repo`.

It contains metric packets, answer paths, trusted artifacts, eval questions, trusted SQL, and validation scripts for the first 10-metric trust-layer style workflow.

Full install path, pricing, and roadmap: <https://getchatdata.com>.
