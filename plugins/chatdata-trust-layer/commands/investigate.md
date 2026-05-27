---
description: Run principal-level KPI, root-cause, data-quality, or recurring business analysis.
---

# Investigate

Use this command for KPI movement, root-cause analysis, data-quality concerns, or recurring business questions.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard --company-repo
```

If the company context repo is missing, stop and run `/chatdata:company-repo` before investigating. If it exists, read it and continue without asking.

Then follow the ChatData principal workflow:

1. Route the question as quick lookup, guided analysis, deep investigation, or presentation-ready analysis.
2. Frame the question around decision, metric, grain, time range, trusted source, edge cases, and success criteria.
3. Read metric trust packets, approved answer paths, corrections, and trusted artifacts before raw discovery.
4. Run data-quality preflight before presenting numbers.
5. For "numbers look wrong" cases, run independent checks across date, segment, status, nulls, recent samples, outliers, trend, and week-over-week movement.
6. Validate with structural, logical, business-rule, source tie-out, and Simpson's Paradox checks.
7. Return the answer with confidence, caveats, evidence, next action, owner, and follow-up date.
8. Record a proof receipt if the workflow produced a useful decision artifact.
9. Run `/chatdata:sync-context` as its own final step after any proof, metric, correction, answer-path, decision, or eval write.

Required output:

- one-sentence answer
- decision implication
- evidence used
- validation and confidence
- caveats
- next action and owner
- proof receipt path if recorded
- context sync status
