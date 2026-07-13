# Submission Links and Test-Case Outline

**Student:** Bruno Pedro  
**Student ID:** 22074709

## Public links

- Git repository: <https://github.com/brunopedro2910/DESD>
- Project management board: **PROJECT_BOARD_URL_REQUIRED**

I will open both links in a private browser window before submission and confirm that tutors can access them without requesting permission.

## Test cases I implemented

- **TC-001:** I implemented producer registration with business details, a producer role and a protected producer profile.
- **TC-002:** I implemented customer registration with contact details, terms acceptance and a saved delivery address.
- **TC-003:** I implemented producer-owned product creation with price, stock, season, allergens, dates and optional images.
- **TC-004:** I implemented available-product browsing across eight categories.
- **TC-005:** I implemented case-insensitive search across product names, descriptions and producer names.
- **TC-006:** I implemented persistent baskets with add, update, remove, stock validation and producer information.
- **TC-007:** I implemented single-producer checkout with a simulated payment, 48-hour lead time and 5/95 financial split.
- **TC-008:** I implemented one customer transaction that creates separate supplier orders for each producer.
- **TC-009:** I implemented a producer-only dispatch board containing delivery, customer, product and financial details.
- **TC-010:** I implemented controlled order-status progression, customer notifications, update notes and an audit timeline.
- **TC-011:** I implemented producer-owned inventory editing, stock deduction, low-stock thresholds and unavailable-product filtering.
- **TC-012:** I implemented seven-day settlement generation from delivered supplier orders and producer settlement history.
- **TC-013:** I implemented Haversine food-mile calculations from producer coordinates to Bristol city centre.
- **TC-014:** I implemented organic product records and an organic-only market filter.
- **TC-015:** I implemented reusable allergens, allergen notes and product-page warnings.
- **TC-016:** I implemented seasonal start/end months, wrap-around season logic and visible season status.
- **TC-017:** I implemented community accounts whose checkouts are recorded as bulk orders with instructions.
- **TC-018:** I implemented restaurant recurring schedules with create, pause, resume and cancel controls.
- **TC-019:** I implemented time-limited surplus offers with validated 10-50% discounts and discounted basket pricing.
- **TC-020:** I implemented producer stories and recipes that can be linked to relevant products.
- **TC-021:** I implemented order history, availability-aware reordering and downloadable CSV receipts.
- **TC-022:** I implemented password validation and hashing, CSRF protection, login throttling, login audits, secure-session options and role/ownership checks.
- **TC-023:** I implemented product-specific low-stock thresholds and producer notifications after checkout.
- **TC-024:** I implemented verified-purchase reviews, one review per customer/product, rating summaries and producer-response storage.
- **TC-025:** I implemented staff-only 5% commission reporting with date/producer filters and CSV export.

The detailed implementation map is in `docs/TEST_CASE_COVERAGE.md`. My automated suite currently contains 26 passing tests, and I will demonstrate the supplied user-facing scenarios manually during the assessment.
