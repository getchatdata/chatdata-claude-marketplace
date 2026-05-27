---
description: Check SQL, charts, metric packets, and answers before they reach stakeholders.
---

# Validate

Use this command to review an existing analysis, SQL query, chart, metric packet, or answer path before it is shared.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard --company-repo
```

If the company context repo is missing, stop and run `/chatdata:company-repo` before validating shared work. If it exists, read the relevant metric packets, answer paths, corrections, sources, and decisions before judging the output.

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
- context sync status after running `/chatdata:sync-context` as its own final step when validation writes proof, corrections, metric changes, answer paths, or evals
