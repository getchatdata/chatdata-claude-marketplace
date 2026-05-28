# ChatData Plugin Scenario Prompts

Use these prompts to test the plugin against the synthetic retail dataset.

## First-Session Proof

```text
/chatdata:start
Use data/plugin-test-datasets/retail_clean/orders.csv.
I own weekly retail performance. Help me prove why profit changed in Q4 2025.
```

Expected behavior:

- frame decision, metric, grain, time range, source, edge cases
- create or reference `gross_profit` and `gross_margin_rate` metric packets
- flag December 2025 as a partial month
- identify West/Furniture/Tables discounting as a major driver
- record a proof receipt

## Data Quality Preflight

```text
/chatdata:validate data/plugin-test-datasets/retail_messy/orders_messy.csv before I use it for a WBR.
```

Expected behavior:

- block final answer until issues are addressed
- find duplicates, null ship dates, negative quantities, impossible discounts, missing regions
- call out partial December 2025
- produce confidence grade below high

## Root Cause Investigation

```text
/chatdata:investigate why gross margin fell in Q4 2025 versus Q3 2025.
Use data/plugin-test-datasets/retail_clean/orders.csv.
```

Expected behavior:

- compare Q4 2025 to Q3 2025
- segment by region, category, sub-category, channel, and store type
- identify discount pressure in West/Furniture/Tables
- separate sales growth from profit deterioration

## Simpson's Paradox Check

```text
/chatdata:investigate whether discounting improved sales without hurting margin.
Use data/plugin-test-datasets/retail_clean/orders.csv.
```

Expected behavior:

- avoid aggregate-only conclusion
- compare discount bands by category and region
- flag that aggregate sales can rise while segment margin deteriorates

## Proof Pack

```text
/chatdata:proof
```

Expected behavior:

- list proof receipts
- estimate time/value only when assumptions are stated
- keep proof export available even after trial expiry
