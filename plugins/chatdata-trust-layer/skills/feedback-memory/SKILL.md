---
description: Apply when the user corrects a number, metric definition, SQL join, caveat, source, or preferred communication style.
---

# Feedback Memory

When the user corrects ChatData, capture the reusable lesson in project state:

- correction category
- affected metric or table
- wrong behavior
- correct behavior
- source or owner if known
- date captured

Store durable corrections under `.chatdata/corrections/` when the correction changes future analysis. Do not block the current answer if capture fails.

Before writing SQL or presenting a recurring metric, check corrections and known caveats so ChatData does not repeat mistakes.
