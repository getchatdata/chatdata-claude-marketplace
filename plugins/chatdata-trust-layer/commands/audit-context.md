---
description: Grade whether the shared repo is ready for reliable company analysis.
---

# Audit Context

Use this command to inspect whether the shared company context is healthy enough for reliable analysis.

First run the company repo guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard --company-repo
```

Then audit the repo in this order:

1. Synced context: metric packets, answer paths, corrections, sources, decisions, playbooks, evals.
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

Do not silently fix shared context during an audit. Show the proposed diff or write-back plan first.

Run the deterministic audit:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" audit-context
```

For release-gate behavior, use strict mode:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" audit-context --strict
```

Strict mode exits non-zero when the repo grades C or D. Treat that as a block on final stakeholder-facing answers until the critical gaps are fixed.
