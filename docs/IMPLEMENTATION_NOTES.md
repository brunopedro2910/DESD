# My Implementation Notes

I designed Gather as one cohesive marketplace domain so I can follow a customer transaction from product discovery through to producer settlement without inherited modules or duplicated ownership boundaries.

## Main design decisions

- I use a custom Django user model with customer, producer, community and restaurant roles.
- I keep producer business information separate from login credentials.
- I store one customer `Order` and create one `SupplierOrder` for each producer represented in the basket.
- I lock product rows inside an atomic checkout transaction before checking and deducting stock.
- I calculate commission per supplier allocation using exact decimal arithmetic.
- I record a local simulated payment reference instead of accepting real financial information.
- I keep supplier status changes as audit events with the responsible user, time and optional note.
- I generate seven-day settlement records from delivered supplier orders with an idempotent command.
- I use PostgreSQL for persistent data and Redis for caching/login throttling in Docker.
- I use a local in-memory cache while running isolated SQLite tests.

## Security boundaries

- Django password validators and hashing protect credentials.
- CSRF middleware protects state-changing browser forms.
- Login attempts are throttled and recorded without storing passwords.
- Customers cannot create producer products through either pages or the API.
- Producers can only edit their products and update their supplier-order portions.
- Customer order APIs only return orders owned by the signed-in customer.
- Financial reports require a staff account.

## Verification

I run migrations, Django checks, 26 automated tests, Docker health checks and live page checks before submission. The detailed mapping is in `TEST_CASE_COVERAGE.md`.
