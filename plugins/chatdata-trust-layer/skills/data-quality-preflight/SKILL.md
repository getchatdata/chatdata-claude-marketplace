---
description: Apply before presenting numbers, when connecting data, or when results look wrong.
---

# Data Quality Preflight

Run enough checks to know whether the data can support the answer:

- row counts
- primary key and duplicate checks
- null rates in analysis columns
- date coverage and freshness
- impossible values
- segment coverage
- join cardinality
- unexpected zeros
- source tie-out to a trusted dashboard, query, or known answer

Severity:

- blocker: halt and explain what must be fixed
- warning: proceed only with visible caveat
- info: note only if it changes interpretation

Never bury a data-quality issue behind confident prose.
