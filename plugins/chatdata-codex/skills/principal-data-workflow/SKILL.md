---
name: principal-data-workflow
description: Use ChatData's principal data workflow in Codex for analytics, metric investigation, WBR prep, validation, and shared company context work.
---

# ChatData Principal Data Workflow

Use this skill when the user asks Codex to analyze data, investigate a KPI, validate a chart or SQL query, create metric definitions, prep a WBR, or work with ChatData company context.

ChatData's core is not tied to Claude Code. In Codex, use the bundled helper and artifacts. Resolve this path relative to this skill file:

```bash
python3 ../../bin/chatdata_state.py <command>
```

## Required Flow

1. Check trial/license state before value work:

```bash
python3 ../../bin/chatdata_state.py guard
```

2. For company or team work, require the shared company repo:

```bash
python3 ../../bin/chatdata_state.py guard --company-repo
```

If it is missing, set it up or attach from email domain:

```bash
python3 ../../bin/chatdata_state.py company-repo --email "<user@company.com>"
```

3. Read company context before raw discovery:

- `metrics/`
- `answer-paths/`
- `corrections/`
- `sources/`
- `decisions/`
- `playbooks/`
- `evals/`

4. For non-trivial analysis, frame:

- question
- decision
- metric
- grain
- time range
- trusted source
- edge cases
- success criteria

5. Run data-quality preflight before numbers:

- row counts
- nulls
- date coverage
- duplicates
- impossible values
- freshness
- segment coverage
- source tie-outs

6. Validate material conclusions:

- structural checks
- logical checks
- business-rule checks
- source tie-out
- Simpson's Paradox / segment reversal
- confidence grade

7. Write reusable context back:

- metric packet
- answer path
- correction
- proof receipt
- decision note
- eval case

## Output

Return:

- one-sentence answer
- decision implication
- evidence used
- validation and confidence
- caveats
- next action and owner
- shared repo write-back recommendation

Keep outputs ChatData-branded. Do not mention private inspiration sources.
