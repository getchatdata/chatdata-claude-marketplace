# ChatData Retail Dataset Dictionary

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
