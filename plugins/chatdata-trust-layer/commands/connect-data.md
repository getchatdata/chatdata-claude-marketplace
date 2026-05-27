---
description: Remember a CSV, warehouse, repo, dashboard, or MCP source for trusted analysis.
---

# Connect Data

Use this command when the user wants ChatData to remember a CSV directory, DuckDB file, warehouse/MCP source, or existing repo as an analysis source.

First run the trial/license guard:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" guard
```

If active, collect the source name, kind, and path in one short prompt if not already provided. Then run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/chatdata_state.py" connect-data --name "<name>" --kind "<csv|duckdb|warehouse|mcp|repo>" --path "<path-or-identifier>" --notes "<optional notes>"
```

After recording the source, inspect enough schema or docs to create the first metric trust packet. Do not ask the user to configure more than needed for the first analysis.

If a company repo is configured, run `/chatdata:sync-context` after recording the source so the shared context is current before analysis starts.
