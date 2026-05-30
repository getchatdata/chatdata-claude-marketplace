---
description: Grade whether MCP-backed shared context is ready for reliable company analysis.
---

# Audit Context

Use this command to inspect whether MCP-backed shared company context is healthy enough for reliable analysis.

First use the ChatData MCP server and run `chatdata_doctor`.

- If the tool is unavailable, stop and say: "ChatData MCP is not connected. Install or repair the MCP from ChatData Settings, then rerun `/chatdata:audit-context`."
- If `chatdata_doctor` reports config, consent, or hub errors, stop and show the exact failing check plus the next install/repair command.
- If healthy, continue.

Then use the ChatData MCP server in this order:

1. `chatdata_pull_context` to refresh approved context into the local MCP cache.
2. `chatdata_export_bundle` to inspect the approved bundle shape.
3. `chatdata_list_conflicts` to identify blocked definitions, duplicate context, or unresolved review issues.
4. `chatdata_search_context` for the top metrics, answer paths, corrections, sources, decisions, playbooks, and evals relevant to the current workspace.

If the MCP context pull is healthy but sparse, grade that as a product/readiness gap rather than falling back silently to old local files.

Run the legacy company repo guard only for diagnostic comparison or local-only trial work:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard --company-repo
```

Then audit shared context in this order:

1. Synced MCP context: metric packets, answer paths, corrections, sources, decisions, playbooks, evals.
2. Scope: count active metrics and recurring questions. Flag broad scope with thin context.
3. Coverage: every important metric should have owner, source, formula, grain, caveats, and validation.
4. MECE: flag duplicate metrics, conflicting formulas, ambiguous columns, or two answer paths for the same question.
5. Tests: inspect `evals/` and list missing tests for top metrics, time scoping, ambiguity, partial periods, and rejected metrics.
6. Bloat: flag files that are too large, stale, duplicated, or private-user-specific.

Return:

- one-paragraph health summary
- critical gaps that can cause wrong answers
- easiest fixes
- recommended next command: `/chatdata:metrics`, `/chatdata:validate`, `/chatdata:proof`, or `/chatdata:benchmark`

Do not silently fix shared context during an audit. Show the proposed diff or MCP write-back plan first.

Run the deterministic local audit only after the MCP audit, or when the user explicitly asks for local repo diagnostics:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" audit-context
```

For release-gate behavior, use strict mode:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" audit-context --strict
```

Strict mode exits non-zero when the local repo grades C or D. Treat MCP critical gaps, unresolved conflicts, or an unhealthy doctor result as a block on final stakeholder-facing answers until fixed.

Required output:

- MCP doctor status
- pulled revision or exact pull blocker
- approved context counts from MCP export
- conflict count and highest-risk conflicts
- readiness grade
- critical gaps that can cause wrong answers
- easiest fixes and the MCP write tool or plugin command that should be used next
