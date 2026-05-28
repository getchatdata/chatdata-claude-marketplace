# ChatData Plugin Test Datasets

Synthetic retail datasets for testing ChatData for Claude Code.

These files are public-safe and generated locally. They are inspired by common retail analytics samples, especially Tableau Superstore-style order-line data, but they do not copy vendor sample rows.

## Files

| Path | Purpose |
| --- | --- |
| `retail_clean/orders.csv` | Clean order-line dataset for first-session demos and root-cause workflows. |
| `retail_messy/orders_messy.csv` | Messy variant for validation and data-quality preflight. |
| `metric_packets/*.yaml` | Demo metric trust packets, including one rejected legacy definition. |
| `data_dictionary.md` | Schema, data quality notes, and known business truths. |
| `scenario_prompts.md` | Prompts for testing `/chatdata:start`, `/chatdata:validate`, `/chatdata:investigate`, and `/chatdata:proof`. |
| `expected_answers.md` | Answer key for root-cause and data-quality tests. |
| `scripts/generate_retail_pack.py` | Reproducible generator. |

## Why This Dataset Works

- familiar retail sales/profit shape
- line-level transactions that can roll up to order, month, segment, region, category, and product
- clean enough for demos
- messy enough to test whether ChatData catches bad inputs
- has a known root cause: Q4 2025 West/Furniture/Tables discounting pressures profit and margin

## Regenerate

```bash
python3 data/plugin-test-datasets/scripts/generate_retail_pack.py
```

## Recommended First Test

```text
/chatdata:investigate why gross margin fell in Q4 2025 versus Q3 2025.
Use data/plugin-test-datasets/retail_clean/orders.csv.
```
