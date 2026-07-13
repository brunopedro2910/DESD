# Test-Case Coverage Map

I use this file as my technical map from the supplied assessment scenarios to the implemented Gather features.

## Scenario mapping

| Case | Where I implemented it | How I verify it |
|---|---|---|
| TC-001 | `RegistrationForm`, `Producer`, `/register/` | Producer role and password boundaries are tested. |
| TC-002 | `RegistrationForm`, `Address`, `/register/` | Customer creation and password behaviour are tested. |
| TC-003 | `ProductForm`, `/producer/products/new/`, producer API create endpoint | Producer creation is tested; customer product creation is blocked. |
| TC-004 | Product list view, categories, availability and stock filters | Public catalogue and filtering are tested. |
| TC-005 | Product search across name, description and producer | Search and empty-result behaviour are tested. |
| TC-006 | `Cart`, `CartItem`, add/update/remove basket views | Quantity handling and stock validation are tested. |
| TC-007 | `checkout_cart`, `PaymentTransaction`, `SupplierOrder` | Checkout, payment record, stock and lead-time rules are tested. |
| TC-008 | Producer grouping inside checkout service | Multi-producer order splitting is tested. |
| TC-009 | `/producer/orders/` producer-scoped query | Cross-producer access is tested. |
| TC-010 | `SupplierOrderEvent` and controlled status actions | Status progression, notes and audit ownership are tested. |
| TC-011 | Product stock, availability and low-stock threshold fields | Stock deduction and invalid stock cases are tested. |
| TC-012 | `generate_weekly_settlements` and `Settlement` | Settlement totals for delivered orders are tested. |
| TC-013 | `Producer.food_miles` property | Demonstrated on product detail pages. |
| TC-014 | `Product.organic` and `?organic=true` | Organic filtering is tested. |
| TC-015 | `Allergen`, allergen notes and product detail output | Demonstrated through product records and forms. |
| TC-016 | `Product.in_season`, `season_start`, `season_end` | Demonstrated with normal and wrap-around season records. |
| TC-017 | Community role and `Order.is_bulk` | Bulk checkout behaviour is tested. |
| TC-018 | `RecurringOrder`, `/recurring/`, pause/resume/cancel action | Ownership and pause behaviour are tested. |
| TC-019 | `SurplusDeal`, validation and discounted active price | Discounted pricing is tested. |
| TC-020 | `Story`, `Recipe` and product relationships | Demonstrated through producer content forms and journal pages. |
| TC-021 | `/account/orders/`, reorder action and receipt CSV | Reorder uses the same stock-safe cart logic. |
| TC-022 | Django auth, `SecureLoginView`, `LoginAudit`, CSRF and role checks | Hashing, audit logging and permission boundaries are tested. |
| TC-023 | Low-stock calculation and `Notification` | Producer notification creation is tested. |
| TC-024 | Review ownership, completed-order check and unique constraint | Demonstrated with delivered order data. |
| TC-025 | Staff finance report, date/producer filters and CSV export | Staff denial, totals and CSV export are tested. |

## Automated command

```powershell
docker compose run --rm --no-deps -e USE_SQLITE=true -e DJANGO_DEBUG=true --entrypoint python -w /app/fresh_exchange web manage.py test marketplace
```

The suite has **26 passing tests**. I still use the supplied 25 cases for the live presentation because several of them are easier to show as end-to-end user journeys than as one isolated unit test.
