# Expected Answers

Use this file as an answer key when testing ChatData. Values are generated from `retail_clean/orders.csv`.

## Q4 2025 Gross Margin Versus Q3 2025

| Period | Rows | Sales | Profit | Gross Margin Rate |
| --- | ---: | ---: | ---: | ---: |
| 2025-Q3 | 225 | $156,255.37 | $23,644.07 | 15.13% |
| 2025-Q4 | 199 | $132,327.46 | $17,063.89 | 12.90% |

Expected conclusion: Q4 2025 gross margin is lower than Q3 2025. The answer should not stop at the aggregate. It should investigate segments and call out discount pressure.

## Main Root Cause

Worst Q4 2025 profit segment:

- Region: `West`
- Category: `Furniture`
- Sub-category: `Tables`
- Rows: 5
- Sales: $6,232.94
- Profit: $-781.77
- Gross margin rate: -12.54%

Expected conclusion: West/Furniture/Tables is a key driver of profit deterioration because discounting became aggressive in Q4 2025.

## Required Caveats

- December 2025 is partial and should not be treated as a complete month.
- Aggregate sales can hide segment-level margin damage.
- The rejected `margin_rate_legacy` packet should not be used for final answers.

## Messy Dataset Expected Findings

`retail_messy/orders_messy.csv` should trigger:

- duplicate order-line checks
- missing ship date checks
- negative quantity checks
- impossible discount checks
- missing region checks
- partial-period warning

Final answers from the messy dataset should be blocked or marked below high confidence until the issues are handled.
