---
description: Check SQL, charts, metric packets, and answers before they reach stakeholders.
---

# Validate

Use this command to review an existing analysis, SQL query, chart, metric packet, or answer path before it is shared.

First verify shared context through MCP:

1. Use the ChatData MCP server and run `chatdata_doctor`.
2. If healthy, run `chatdata_pull_context` before reading trust artifacts.
3. If MCP is unavailable or unhealthy, stop stakeholder-facing validation and guide MCP setup. Continue local-only only when the user explicitly accepts that shared context will not sync.

Then run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard --company-repo
```

If the company context repo is missing but MCP context is healthy, continue from MCP context. If both MCP and local shared context are missing, stop and run MCP setup before validating shared work.

Apply the ChatData validation stack:

1. Structural: schema, primary key, completeness, referential integrity.
2. Logical: totals versus parts, segment exhaustiveness, time continuity, date scope.
3. Business rules: plausible ranges, known exclusions, freshness, denominator sanity.
4. Source tie-out: trusted dashboard, approved SQL, metric packet, or benchmark.
5. Simpson's Paradox: check whether aggregate conclusions reverse in key segments.

Return:

- pass/block status
- confidence grade
- findings that must be fixed before sharing
- caveats that can be carried into the output
- recommendation to publish, revise, or refuse
- context sync status after running `/chatdata:sync-context` as its own final step when validation writes proof, corrections, metric changes, answer paths, or evals. That sync must write reusable artifacts through MCP first.
