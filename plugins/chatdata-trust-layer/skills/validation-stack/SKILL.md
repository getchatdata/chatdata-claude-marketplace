---
description: Apply after analysis and before final answers, exports, WBRs, memos, or proof receipts.
---

# ChatData Validation Stack

Before a material conclusion is shared, validate it through:

1. Structural: schema, keys, completeness, referential integrity.
2. Logical: parts sum to whole, segment coverage, trend continuity.
3. Business rules: plausible ranges, exclusions, denominator sanity, freshness.
4. Source tie-out: benchmark SQL, blessed dashboard, semantic object, or owner-reviewed answer path.
5. Simpson's Paradox: aggregate conclusion versus key segments.

Output a visible confidence grade:

- high: multiple checks pass and source tie-out is clean
- medium: useful but caveated or single-source
- low: exploratory, incomplete, or owner review needed

Block final export when a blocker remains.
