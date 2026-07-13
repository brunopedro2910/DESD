# Implementation Notes

This file is my short technical explanation of how I built Gather and why the main parts are arranged the way they are.

## Domain shape

I treated the case study as a marketplace with four account types:

- customers who buy food;
- producers who sell and dispatch food;
- restaurants that may need repeat ordering;
- community buyers that may place bulk orders.

That structure is handled with one custom Django user model and role-specific rules around the pages, forms and API endpoints.

## Checkout and order handling

The checkout flow is the part I kept most carefully controlled. When a basket is checked out, the service layer:

1. locks the selected product rows;
2. checks stock and producer lead-time rules;
3. deducts stock;
4. creates the customer order;
5. creates one supplier order per producer;
6. calculates BRFN commission and producer payout;
7. records a simulated payment reference;
8. sends producer/customer notifications.

I kept this in the service layer so the behaviour is not scattered through templates or views.

## Producer boundaries

Producer data is deliberately scoped. A producer can edit their own catalogue, manage their own supplier orders and see their own settlement history. They cannot change another producer's products or order lines.

Customers have the same kind of ownership boundary for baskets, addresses, orders, reviews and API responses.

## Finance rules

The project uses a local simulated payment provider because the assessment does not need real card processing. Supplier-order totals are split into:

- 5% BRFN commission;
- 95% producer payout.

Weekly settlements are generated from delivered supplier orders. The command is idempotent, so I can rerun it during testing without creating duplicate settlement rows.

## Security choices

The implementation uses Django's normal security features and adds a few project-specific checks:

- password validation and hashing;
- CSRF protection on forms;
- login-attempt records;
- cache-backed login throttling in Docker;
- staff-only finance reporting;
- role checks for producer and customer actions;
- ownership checks in page views and API views.

## Verification

Before submission I checked migrations, Django system checks, Docker startup, API health, browser pages and the automated suite. The detailed case-study mapping is in `docs/TEST_CASE_COVERAGE.md`.
