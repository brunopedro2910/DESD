# Gather Bristol Marketplace

I built Gather as my individual DESD resit project for the Bristol Regional Food Network case study.

**Author:** Bruno Pedro  
**Student ID:** 22074709  
**Contribution:** 100%

## What I implemented

Gather is a Django and Django REST Framework marketplace that connects customers with food producers around Bristol. My implementation includes:

- customer, producer, community-group and restaurant accounts;
- producer profiles, seasonal products, stock, allergens and food-mile information;
- category browsing, product search and organic filters;
- persistent baskets containing products from several producers;
- one customer checkout split into separate supplier orders;
- a minimum 48-hour preparation rule for every producer;
- a simulated assessment payment record with no real financial data;
- an exact 5% network commission and 95% producer allocation;
- producer-only dispatch views, controlled status transitions, notes and audit events;
- weekly settlement generation and producer settlement history;
- recurring restaurant schedules with pause, resume and cancellation controls;
- surplus offers, verified reviews, recipes, stories and low-stock notifications;
- staff-only financial filters and CSV exports;
- login throttling, login audit records and role/ownership permissions;
- an ownership-scoped REST API.

The demonstration catalogue contains 41 products across eight categories and four producers.

## Project structure

```text
fresh_exchange/
|-- exchange/        Django configuration
|-- marketplace/     Models, services, forms, views, API and tests
|-- manage.py
docker/              Container entrypoint
deployment/          Optional Nginx configuration
```

I keep checkout and settlement rules in `fresh_exchange/marketplace/services.py`. Checkout uses one database transaction to lock stock, validate preparation dates, create supplier orders, calculate commission, record the simulated payment and send notifications.

## Run with Docker

```bash
docker compose up --build
```

Open [http://localhost:8000/](http://localhost:8000/).

The standard environment starts three containers:

- `web` - Django and Gunicorn;
- `db` - PostgreSQL;
- `redis` - cache and login-throttling storage.

The first startup applies migrations, collects static files and loads deterministic demonstration data. A later startup safely checks the same data without duplicating it.

## Demonstration accounts

All demonstration accounts use the password `GatherDemo!2026`.

| Role | Username |
|---|---|
| Customer | `gather_customer` |
| Producer | `gather_producer` |
| Restaurant | `gather_restaurant` |
| Administrator | `gather_admin` |

These accounts and payment records are for local assessment testing only.

## Run tests

```powershell
docker compose run --rm --no-deps -e USE_SQLITE=true -e DJANGO_DEBUG=true --entrypoint python -w /app/fresh_exchange web manage.py test marketplace
```

My automated suite contains 26 tests covering browsing, search, stock protection, basket updates, multi-producer checkout, lead times, commission calculations, simulated payments, settlement generation, recurring orders, login auditing, API permissions, ownership boundaries, financial CSV exports and password hashing.

## Weekly settlements

Generate or refresh the current seven-day settlement records from delivered supplier orders:

```powershell
docker compose exec -w /app/fresh_exchange web python manage.py generate_settlements
```

## Main URLs

| Area | URL |
|---|---|
| Marketplace | `/market/` |
| Basket | `/basket/` |
| Customer account | `/account/` |
| Producer operations | `/producer/` |
| Producer dispatch board | `/producer/orders/` |
| Restaurant schedules | `/recurring/` |
| Surplus offers | `/surplus/` |
| Stories and recipes | `/stories/` |
| Staff financial report | `/network/financial-report/` |
| API health | `/api/health/` |
| API products | `/api/products/` |

## Submission evidence

- `BRUNO_PEDRO_CONTRIBUTIONS_MATRIX.docx` - my official individual contribution matrix;
- `LINKS_AND_TEST_CASES.md` - repository, project-board and test-case summary;
- `docs/TEST_CASE_COVERAGE.md` - detailed mapping to the 25 supplied cases;
- `SUBMISSION_CHECKLIST.md` - my final manual checks.

I used a local simulated payment gateway because the case study explicitly permits a mock service and prohibits real financial data.
