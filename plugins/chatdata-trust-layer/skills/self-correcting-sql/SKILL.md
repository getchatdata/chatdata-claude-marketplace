---
description: Apply when writing, debugging, or reviewing SQL or warehouse queries.
---

# Self-Correcting SQL Loop

Use a closed loop, not one-shot SQL:

1. State the business question.
2. State grain, joins, filters, and assumptions.
3. Prefer approved SQL patterns and trusted answer paths.
4. Run the smallest safe query first.
5. Use errors or surprising output as feedback.
6. Iterate until the query runs and the logic makes sense.
7. Validate against a trusted benchmark before presenting.

Rules:

- never `SELECT *`
- use date filters when exploring
- avoid changing time windows mid-loop
- do not present valid SQL as a valid answer until the business logic is checked
