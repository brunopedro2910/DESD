# Gather

This is my individual DESD resit implementation for the Bristol Regional Food Network case study.

**Name:** Bruno Pedro  
**Student ID:** 22074709  
**Recorded contribution:** 100%

## Project overview

Gather is a Dockerised Django marketplace for local Bristol food. I built it so the full journey is visible in one system: a customer can discover products, fill a basket, place an order, and each producer then manages only their own part of that order.

The project covers the core case-study areas:

- account registration for customers, producers, restaurants and community buyers;
- producer profiles with delivery lead times, contact details and food-mile information;
- product listings with stock, category, season, allergens, organic status and images;
- browsing, searching and filtering products that are currently available;
- persistent baskets, stock checks and quantity updates;
- checkout with simulated payment records and no real card handling;
- one customer order split into producer-specific supplier orders;
- 48-hour producer preparation validation;
- 5% BRFN commission and 95% producer payout calculation;
- producer dispatch tools, order notes and status history;
- weekly settlement records for delivered producer orders;
- restaurant recurring orders and community bulk-order support;
- surplus discounts, reviews, stories, recipes and notifications;
- staff-only finance reporting with filters and CSV export;
- REST API endpoints with role and ownership protection.

The seed data gives me 41 products, eight product categories and four producers for demonstration.

## How the code is arranged

```text
fresh_exchange/
|-- exchange/          project settings, URLs and WSGI entrypoint
|-- marketplace/       app models, services, forms, views, API and tests
|-- manage.py
docker/                container startup script
deployment/            optional Nginx config
```

Most business rules are kept in `fresh_exchange/marketplace/services.py`. I used that file for checkout, stock locking, supplier-order creation, payment recording, commission calculation, settlement generation and notifications because those actions need to stay consistent across the website and tests.

## Start the project

```bash
docker compose up --build
```

Then open:

<http://localhost:8000/>

The Docker setup runs:

| Container | Purpose |
|---|---|
| `web` | Django app served through Gunicorn |
| `db` | PostgreSQL database |
| `redis` | cache and login-throttling support |

On startup the app applies migrations, collects static files and loads the demonstration data. The seed command is safe to run again because it updates the demo records instead of creating duplicate catalogues.

## Demo logins

Every local demo account uses:

```text
GatherDemo!2026
```

| Role | Username |
|---|---|
| Customer | `gather_customer` |
| Producer | `gather_producer` |
| Restaurant | `gather_restaurant` |
| Administrator | `gather_admin` |

These accounts are only for assessment testing. The payment service is also simulated, so the project never asks for real payment details.

## Test command

```powershell
docker compose run --rm --no-deps -e USE_SQLITE=true -e DJANGO_DEBUG=true --entrypoint python -w /app/fresh_exchange web manage.py test marketplace
```

My automated checks currently cover 26 test cases across registration, permissions, search, baskets, checkout, stock deduction, supplier-order splitting, settlements, recurring orders, login auditing, API access, financial exports and password hashing.

## Useful pages

| Feature area | Path |
|---|---|
| Market catalogue | `/market/` |
| Basket | `/basket/` |
| My account | `/account/` |
| Producer studio | `/producer/` |
| Producer orders | `/producer/orders/` |
| Restaurant schedules | `/recurring/` |
| Surplus food | `/surplus/` |
| Stories and recipes | `/stories/` |
| Finance report | `/network/financial-report/` |
| API health check | `/api/health/` |
| Product API | `/api/products/` |

## Settlement command

To create or refresh weekly settlement rows from delivered supplier orders:

```powershell
docker compose exec -w /app/fresh_exchange web python manage.py generate_settlements
```

## Submission files

I included the evidence files I need for the final submission:

| File | What it is for |
|---|---|
| `BRUNO_PEDRO_CONTRIBUTIONS_MATRIX.pdf` | my individual contribution matrix |
| `BRUNO_PEDRO_SUBMISSION_LINKS.pdf` | PDF copy of my repository, board and test-case links |
| `LINKS_AND_TEST_CASES.md` | Markdown evidence for public links and case coverage |
| `docs/TEST_CASE_COVERAGE.md` | detailed implementation map for the 25 supplied scenarios |
| `SUBMISSION_CHECKLIST.md` | my final submission checks |

I built this version as my own individual submission and all project evidence is recorded under my name.
