# Supplied Test-Case Coverage

I mapped each supplied assessment scenario to the current Gather implementation. The paths and class names below are the evidence I will use during my demonstration.

| ID | Implementation evidence | Automated coverage |
|---|---|---|
| TC-001 | `RegistrationForm`, `Producer`, `/register/` | Password/role boundaries covered |
| TC-002 | `RegistrationForm`, `Address`, `/register/` | New-customer and password behaviour covered |
| TC-003 | `ProductForm`, `/producer/products/new/`, producer API permission | Producer API creation and customer denial covered |
| TC-004 | `ProductList`, categories, available/stock filtering | Public market and filters covered |
| TC-005 | Name, description and producer search | Search and empty-result behaviour covered |
| TC-006 | `Cart`, `CartItem`, add/update/remove views | Quantity and stock validation covered |
| TC-007 | `checkout_cart`, `PaymentTransaction`, `SupplierOrder` | Checkout, stock and payment records covered |
| TC-008 | Producer grouping and one supplier order per producer | Multi-producer split covered |
| TC-009 | `/producer/orders/` with producer-scoped query | Cross-producer denial covered |
| TC-010 | Controlled transitions and `SupplierOrderEvent` notes | Progression, ownership and audit event covered |
| TC-011 | Product stock, availability and low-stock threshold | Deduction and invalid stock covered |
| TC-012 | `generate_weekly_settlements`, `Settlement`, producer history | Delivered-order settlement totals covered |
| TC-013 | `Producer.food_miles` Haversine property | Demonstrated on product detail page |
| TC-014 | `Product.organic` and `?organic=true` | Organic filter covered |
| TC-015 | `Allergen`, notes and product-page display | Demonstrated with product form/detail |
| TC-016 | `Product.in_season` and month range fields | Demonstrated with product records |
| TC-017 | Community role and `Order.is_bulk` | Checkout service behaviour covered |
| TC-018 | `RecurringOrder`, `/recurring/`, pause/resume/cancel action | Ownership and pause action covered |
| TC-019 | `SurplusDeal` validation and active price | Discounted price covered |
| TC-020 | `Story`, `Recipe`, recipe-product relationship and journal | Demonstrated through producer content forms |
| TC-021 | `/account/orders/`, reorder and CSV receipt | Reorder uses the same stock-safe cart service |
| TC-022 | Django validators/hashing, `SecureLoginView`, `LoginAudit`, CSRF, role checks | Hashing, login audit and permission boundaries covered |
| TC-023 | Checkout threshold calculation and `Notification` | Low-stock notification covered |
| TC-024 | Completed-order review check and unique review constraint | Demonstrated using delivered order data |
| TC-025 | Staff-only financial report, filters and CSV export | Staff denial, calculations and CSV export covered |

## Automated verification

```powershell
docker compose run --rm --no-deps -e USE_SQLITE=true -e DJANGO_DEBUG=true --entrypoint python -w /app/fresh_exchange web manage.py test marketplace
```

The suite contains **26 tests**. I use the supplied 25 scenarios for manual presentation coverage because several scenarios contain multiple user-interface steps that are clearer to demonstrate than to claim as a single automated test.
