# Final Links And Scenario Evidence

**Student:** Bruno Pedro  
**Student ID:** 22074709

## Public evidence

| Evidence item | Link |
|---|---|
| GitHub repository | <https://github.com/brunopedro2910/DESD> |
| Notion project board | <https://app.notion.com/p/BRFN-Test-Cases-Task-Board-ae1fabe4c27d82c1b631810d263ac7d9?source=copy_link> |

These are the two public links I am using for my final submission evidence.

## What I will demonstrate

I used the supplied 25 scenarios as my checklist for the system. The table below records where each requirement is covered in my build.

| Case | My implementation evidence |
|---|---|
| TC-001 | Producer sign-up stores business details, assigns the producer role and protects the producer profile. |
| TC-002 | Customer sign-up records contact details, terms acceptance and a delivery address. |
| TC-003 | Producers can create their own products with price, stock, season, allergens, dates and optional images. |
| TC-004 | The market page shows available products across eight categories. |
| TC-005 | Search checks product names, descriptions and producer names. |
| TC-006 | Baskets are persistent and support add, update, remove and stock validation. |
| TC-007 | Checkout uses a simulated payment, validates the 48-hour rule and applies the 5/95 split. |
| TC-008 | A mixed basket becomes one customer order with separate supplier orders for each producer. |
| TC-009 | Producers have a private order board showing only their own delivery, customer and payout details. |
| TC-010 | Supplier orders move through controlled statuses with notes and an audit trail. |
| TC-011 | Producer stock is deducted, low-stock thresholds are checked and unavailable items are hidden. |
| TC-012 | Delivered supplier orders can be converted into seven-day settlement records. |
| TC-013 | Food miles are calculated from producer coordinates to Bristol city centre. |
| TC-014 | Organic products can be recorded and filtered separately. |
| TC-015 | Allergens and allergen notes are stored and shown on product pages. |
| TC-016 | Seasonal start and end months support normal and wrap-around growing seasons. |
| TC-017 | Community accounts can place bulk orders with extra instructions. |
| TC-018 | Restaurant recurring schedules can be created, paused, resumed and cancelled. |
| TC-019 | Surplus offers support validated 10-50% discounts and time-limited pricing. |
| TC-020 | Producers can publish stories and recipes linked to products. |
| TC-021 | Customers can view order history, reorder available items and download CSV receipts. |
| TC-022 | Password hashing, validation, CSRF, login throttling, login audit records and role checks are active. |
| TC-023 | Low-stock producer notifications are generated after checkout. |
| TC-024 | Reviews require a completed purchase and one customer can review each product once. |
| TC-025 | Staff users can view and export the 5% commission finance report. |

For more detail, I use `docs/TEST_CASE_COVERAGE.md` as my technical demonstration map. My automated test suite contains 26 passing tests, and the remaining user-facing behaviour is prepared for manual presentation.
