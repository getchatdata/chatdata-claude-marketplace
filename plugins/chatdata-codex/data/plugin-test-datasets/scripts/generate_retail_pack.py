#!/usr/bin/env python3
"""Generate synthetic retail datasets for ChatData plugin testing."""

from __future__ import annotations

import csv
import random
import shutil
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED = 240526
ROW_COUNT = 2600


REGIONS = {
    "West": [
        ("Los Angeles", "California", "90001"),
        ("Seattle", "Washington", "98101"),
        ("Denver", "Colorado", "80202"),
        ("Portland", "Oregon", "97201"),
    ],
    "East": [
        ("New York", "New York", "10001"),
        ("Boston", "Massachusetts", "02108"),
        ("Philadelphia", "Pennsylvania", "19103"),
        ("Washington", "District of Columbia", "20001"),
    ],
    "Central": [
        ("Chicago", "Illinois", "60601"),
        ("Dallas", "Texas", "75201"),
        ("Minneapolis", "Minnesota", "55401"),
        ("St. Louis", "Missouri", "63101"),
    ],
    "South": [
        ("Atlanta", "Georgia", "30303"),
        ("Miami", "Florida", "33101"),
        ("Charlotte", "North Carolina", "28202"),
        ("Nashville", "Tennessee", "37201"),
    ],
}

PRODUCTS = {
    "Furniture": [
        ("Bookcases", "Modular bookcase"),
        ("Chairs", "Ergonomic office chair"),
        ("Tables", "Conference table"),
        ("Furnishings", "Desk lamp"),
    ],
    "Office Supplies": [
        ("Binders", "Heavy duty binder"),
        ("Paper", "Copy paper"),
        ("Storage", "Archive box"),
        ("Labels", "Shipping labels"),
    ],
    "Technology": [
        ("Phones", "Desk phone"),
        ("Accessories", "Wireless keyboard"),
        ("Copiers", "Office copier"),
        ("Machines", "Label printer"),
    ],
}

BASE_PRICE = {
    "Bookcases": 440,
    "Chairs": 290,
    "Tables": 720,
    "Furnishings": 85,
    "Binders": 24,
    "Paper": 18,
    "Storage": 52,
    "Labels": 14,
    "Phones": 220,
    "Accessories": 65,
    "Copiers": 980,
    "Machines": 360,
}

MARGIN = {
    "Bookcases": 0.18,
    "Chairs": 0.24,
    "Tables": 0.12,
    "Furnishings": 0.28,
    "Binders": 0.32,
    "Paper": 0.26,
    "Storage": 0.30,
    "Labels": 0.34,
    "Phones": 0.22,
    "Accessories": 0.31,
    "Copiers": 0.21,
    "Machines": 0.17,
}

SEGMENTS = ["Consumer", "Corporate", "Home Office"]
SHIP_MODES = ["Standard Class", "Second Class", "First Class", "Same Day"]
CHANNELS = ["organic", "paid_search", "email", "sales_assist", "partner"]
STORE_TYPES = ["existing", "new"]


def main() -> None:
    random.seed(SEED)
    for name in ["retail_clean", "retail_messy"]:
        shutil.rmtree(ROOT / name, ignore_errors=True)
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    rows = generate_clean_rows()
    write_csv(ROOT / "retail_clean" / "orders.csv", rows)
    write_csv(ROOT / "retail_messy" / "orders_messy.csv", make_messy_rows(rows))
    write_dictionary(ROOT / "data_dictionary.md")
    write_scenarios(ROOT / "scenario_prompts.md")
    write_expected_answers(ROOT / "expected_answers.md", rows)
    write_metric_packets(ROOT / "metric_packets")
    write_readme(ROOT / "README.md")


def generate_clean_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    start = date(2023, 1, 1)
    end = date(2025, 12, 15)
    day_span = (end - start).days

    for row_id in range(1, ROW_COUNT + 1):
        order_date = start + timedelta(days=random.randint(0, day_span))
        if order_date.month == 12 and order_date.year == 2025:
            # Keep latest month intentionally partial for freshness/period checks.
            order_date = date(2025, 12, random.randint(1, 15))
        ship_lag = random.choices([1, 2, 3, 4, 5, 7], weights=[18, 28, 24, 16, 9, 5])[0]
        ship_date = order_date + timedelta(days=ship_lag)
        region = random.choices(["West", "East", "Central", "South"], weights=[31, 27, 22, 20])[0]
        city, state, postal_code = random.choice(REGIONS[region])
        category = random.choices(["Furniture", "Office Supplies", "Technology"], weights=[28, 42, 30])[0]
        sub_category, product_name = random.choice(PRODUCTS[category])
        quantity = random.choices([1, 2, 3, 4, 5, 6, 8, 10], weights=[20, 26, 20, 14, 8, 6, 4, 2])[0]
        base_price = BASE_PRICE[sub_category] * random.uniform(0.78, 1.22)
        discount = choose_discount(order_date, region, category, sub_category)
        sales = round(base_price * quantity * (1 - discount), 2)
        margin = MARGIN[sub_category]
        profit = round(sales * (margin - discount * 0.62) + random.uniform(-8, 8), 2)
        returned = random.random() < return_probability(order_date, category, ship_lag)

        if returned:
            profit = round(profit - sales * 0.08, 2)

        rows.append(
            {
                "row_id": row_id,
                "order_id": f"CD-{order_date.year}-{100000 + row_id // 3}",
                "order_date": order_date.isoformat(),
                "ship_date": ship_date.isoformat(),
                "ship_mode": random.choice(SHIP_MODES),
                "customer_id": f"C{random.randint(1000, 1499)}",
                "customer_name": f"Customer {random.randint(1000, 1499)}",
                "segment": random.choices(SEGMENTS, weights=[48, 34, 18])[0],
                "country": "United States",
                "city": city,
                "state": state,
                "postal_code": postal_code,
                "region": region,
                "product_id": f"{category[:3].upper()}-{sub_category[:3].upper()}-{random.randint(100, 999)}",
                "category": category,
                "sub_category": sub_category,
                "product_name": product_name,
                "sales": sales,
                "quantity": quantity,
                "discount": round(discount, 2),
                "profit": profit,
                "returned": "true" if returned else "false",
                "acquisition_channel": random.choice(CHANNELS),
                "store_type": random.choices(STORE_TYPES, weights=[86, 14])[0],
            }
        )

    return sorted(rows, key=lambda row: (row["order_date"], row["row_id"]))


def choose_discount(order_date: date, region: str, category: str, sub_category: str) -> float:
    discount = random.choices([0.0, 0.05, 0.1, 0.15, 0.2], weights=[42, 22, 18, 12, 6])[0]
    if order_date >= date(2025, 10, 1) and region == "West" and category == "Furniture":
        discount += random.choices([0.1, 0.2, 0.3], weights=[35, 45, 20])[0]
    if sub_category == "Tables" and order_date >= date(2025, 10, 1):
        discount += 0.1
    return min(discount, 0.65)


def return_probability(order_date: date, category: str, ship_lag: int) -> float:
    probability = 0.025
    if category == "Furniture":
        probability += 0.025
    if ship_lag >= 5:
        probability += 0.018
    if order_date >= date(2025, 10, 1):
        probability += 0.012
    return probability


def make_messy_rows(clean_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = [row.copy() for row in clean_rows]

    duplicate_source_ids = [180, 545, 1040, 1555, 2210]
    for source_id in duplicate_source_ids:
        duplicate = rows[source_id].copy()
        duplicate["row_id"] = f"DUP-{duplicate['row_id']}"
        duplicate["messy_note"] = "duplicate_order_line"
        rows.append(duplicate)

    for index in [41, 222, 619, 1288, 2044]:
        rows[index]["ship_date"] = ""
        rows[index]["messy_note"] = "missing_ship_date"

    for index in [77, 901]:
        rows[index]["quantity"] = -abs(int(rows[index]["quantity"]))
        rows[index]["messy_note"] = "negative_quantity"

    for index in [388, 1337, 2119]:
        rows[index]["discount"] = 1.25
        rows[index]["profit"] = round(float(rows[index]["profit"]) - float(rows[index]["sales"]) * 0.4, 2)
        rows[index]["messy_note"] = "impossible_discount"

    for index in [508, 509, 510, 511, 512, 513]:
        rows[index]["region"] = ""
        rows[index]["messy_note"] = "missing_region"

    for row in rows:
        row.setdefault("messy_note", "")
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_dictionary(path: Path) -> None:
    path.write_text(
        """# ChatData Retail Dataset Dictionary

This pack is synthetic and public-safe. It is modeled after common retail analytics samples such as Tableau Superstore and Microsoft retail demos, but it does not copy vendor sample rows.

## Tables

### retail_clean/orders.csv

Clean order-line data for first-session ChatData plugin demos.

### retail_messy/orders_messy.csv

Same schema plus `messy_note`, with injected issues:

- duplicate order lines
- missing ship dates
- negative quantities
- impossible discounts
- missing regions
- intentionally partial December 2025 period

## Core Fields

| Field | Meaning |
| --- | --- |
| `order_id` | Order identifier. Multiple rows can belong to one order. |
| `order_date` | Order date in ISO format. |
| `ship_date` | Ship date in ISO format. |
| `segment` | Customer segment. |
| `region` | US sales region. |
| `category`, `sub_category`, `product_name` | Product hierarchy. |
| `sales` | Net sales after discount. |
| `quantity` | Units sold. |
| `discount` | Discount rate as decimal, where `0.2` means 20%. |
| `profit` | Net profit after estimated discount/returns impact. |
| `returned` | Whether the order line was returned. |
| `acquisition_channel` | Acquisition source for root-cause segmentation. |
| `store_type` | Existing versus new store. |

## Known Business Truths

- Q4 2025 profit is intentionally pressured by high discounting in West/Furniture, especially Tables.
- December 2025 is intentionally partial. Full-period comparisons should avoid treating it as a complete month.
- Returns rise in Q4 2025, especially for Furniture and slower shipping.
""",
        encoding="utf-8",
    )


def write_scenarios(path: Path) -> None:
    path.write_text(
        """# ChatData Plugin Scenario Prompts

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
""",
        encoding="utf-8",
    )


def write_expected_answers(path: Path, rows: list[dict[str, object]]) -> None:
    def quarter(value: object) -> str:
        text = str(value)
        month = int(text[5:7])
        return f"{text[:4]}-Q{((month - 1) // 3) + 1}"

    def summarize(selected: list[dict[str, object]]) -> tuple[float, float, float]:
        sales = sum(float(row["sales"]) for row in selected)
        profit = sum(float(row["profit"]) for row in selected)
        margin = profit / sales if sales else 0.0
        return sales, profit, margin

    q3_rows = [row for row in rows if quarter(row["order_date"]) == "2025-Q3"]
    q4_rows = [row for row in rows if quarter(row["order_date"]) == "2025-Q4"]
    q3_sales, q3_profit, q3_margin = summarize(q3_rows)
    q4_sales, q4_profit, q4_margin = summarize(q4_rows)

    segment: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    for row in q4_rows:
        key = (str(row["region"]), str(row["category"]), str(row["sub_category"]))
        segment.setdefault(key, []).append(row)
    worst_key, worst_rows = min(segment.items(), key=lambda item: summarize(item[1])[1])
    worst_sales, worst_profit, worst_margin = summarize(worst_rows)

    path.write_text(
        f"""# Expected Answers

Use this file as an answer key when testing ChatData. Values are generated from `retail_clean/orders.csv`.

## Q4 2025 Gross Margin Versus Q3 2025

| Period | Rows | Sales | Profit | Gross Margin Rate |
| --- | ---: | ---: | ---: | ---: |
| 2025-Q3 | {len(q3_rows)} | ${q3_sales:,.2f} | ${q3_profit:,.2f} | {q3_margin:.2%} |
| 2025-Q4 | {len(q4_rows)} | ${q4_sales:,.2f} | ${q4_profit:,.2f} | {q4_margin:.2%} |

Expected conclusion: Q4 2025 gross margin is lower than Q3 2025. The answer should not stop at the aggregate. It should investigate segments and call out discount pressure.

## Main Root Cause

Worst Q4 2025 profit segment:

- Region: `{worst_key[0]}`
- Category: `{worst_key[1]}`
- Sub-category: `{worst_key[2]}`
- Rows: {len(worst_rows)}
- Sales: ${worst_sales:,.2f}
- Profit: ${worst_profit:,.2f}
- Gross margin rate: {worst_margin:.2%}

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
""",
        encoding="utf-8",
    )


def write_metric_packets(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
    (path / "gross_profit.yaml").write_text(
        """metric_id: gross_profit
label: Gross Profit
definition: Net sales minus estimated cost, discount, and return impact.
formula: sum(profit)
grain: order_line
timezone: America/Los_Angeles
blessed_source: data/plugin-test-datasets/retail_clean/orders.csv
filters:
  - exclude rows where quantity <= 0
  - exclude rows where discount < 0 or discount > 1
exclusions:
  - incomplete current period unless explicitly requested
freshness_rule: Data is fresh through the max order_date in the file.
validation_rules:
  - sales and profit totals tie to source CSV
  - row count and duplicate order-line checks pass
  - compare by region, category, and sub_category before final conclusion
owner: ChatData demo
review_status: reviewed
""",
        encoding="utf-8",
    )
    (path / "gross_margin_rate.yaml").write_text(
        """metric_id: gross_margin_rate
label: Gross Margin Rate
definition: Gross profit divided by net sales.
formula: sum(profit) / nullif(sum(sales), 0)
grain: selected reporting grain
timezone: America/Los_Angeles
blessed_source: data/plugin-test-datasets/retail_clean/orders.csv
filters:
  - exclude rows where quantity <= 0
  - exclude rows where discount < 0 or discount > 1
exclusions:
  - incomplete current period unless explicitly requested
freshness_rule: Data is fresh through the max order_date in the file.
validation_rules:
  - denominator must be positive
  - compare aggregate movement to region/category/sub-category movement
  - flag Simpson's Paradox risk when aggregate and segment reads disagree
owner: ChatData demo
review_status: reviewed
""",
        encoding="utf-8",
    )
    (path / "conflicting_margin_definition.yaml").write_text(
        """metric_id: margin_rate_legacy
label: Legacy Margin Rate
definition: Legacy demo definition included to test conflict handling. Do not use for final answers.
formula: avg(profit / nullif(sales, 0))
grain: order_line
timezone: America/Los_Angeles
blessed_source: none
known_issue: This averages row-level ratios and can disagree with the approved gross_margin_rate definition.
review_status: rejected
""",
        encoding="utf-8",
    )


def write_readme(path: Path) -> None:
    path.write_text(
        """# ChatData Plugin Test Datasets

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
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
