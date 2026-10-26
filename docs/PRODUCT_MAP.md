# UI architecture and feature matrix

## Public route map

`/` home → `/shop` catalog filters/search → `/product/:slug` product detail → `/cart` guest cart → `/account` login or register → `/orders` through account list → `/plan` preliminary plot/room-zoning sketch → `/learn` material/construction education → `/privacy` analytics choice → `/about` company introduction.

Public style: architectural evergreen (#163e35), warm ivory (#fbf9f3), sage green, copper accent, high whitespace, responsive product-card grid, illustrative building and material drawings. Desktop header contains brand, large search, account and cart; mobile header stacks search and uses scrolling category links. No external images or analytics services are required by this starter.

## Admin route map

Independent Super and Regional apps are served on separate local ports and future hostnames. Login gates each page; role/region enforcement is **on the API**, not just the sidebar.

| Function | Super | Regional | Current state |
|---|---|---|---|
| Overview with authorized actual counts | Yes | Region-only | Implemented |
| Catalog create/list | Yes | No | Implemented starter |
| Propose regional material rate | Yes | Assigned region | Implemented |
| Approve material rate | Yes, different person | No | Implemented |
| Requests overview | Global | Region-only | Implemented |
| Audit history | Yes | No | Implemented basic |
| Inventory/warehouse management | Planned | Planned | Not implemented |
| Customer segmentation | Planned | Planned aggregate | Not implemented |
| Supplier/quotation operations | Planned | Planned | Order request only |
| Municipality approvals and engineering rules | Planned | Planned review | Not implemented |
| Model provider/AI evaluation controls | Planned | No | Not implemented |

## Requested customer activity event types

`page_viewed`, `product_searched`, `product_clicked`, `price_viewed`, `cart_item_added`, `cart_item_removed`, `plan_started`, `material_compared`, `estimate_created`. The schema allowlist is implemented; only a subset currently has user-interface emitters. Cart/order transactional records are independent of optional analytics. Future funnels need event quality checks and consent-reviewed aggregation.

## Exact feature gaps against the PDF

- Next.js/NestJS: HTML/CSS/JS with FastAPI used for this inspectable local starter. Technical stack differs deliberately, and can be migrated module by module.
- Genuine paid checkout: blocked until provider and operational rules are selected; only order/quote requests exist.
- Product inventory/stock/reservations: pending.
- Nepal plot setback/FAR: not calculated; current SVG is illustrative *zoning*, unscaled; no measured floor plan or 2D CAD editing.
- Detailed BoQ or cost calculation: pending verified quantities and operator-approved work-item rate data.
- AI Gateway: specified, not connected; do not send private customer data to unreviewed models.
- Customer data export/deletion, password recovery, translations, regional location normalization: pending.

## Next engineering stories

1. E2E tests with a real ephemeral PostgreSQL, browser regression tests, and CI scanning.
2. Product/supplier import with SKU uniqueness, stock, images and regional delivery zones.
3. Safe password recovery, email confirmation, user privacy export/erasure and secure admin MFA lifecycle.
4. Shopping order state machine and chosen Nepal payment provider integration.
5. Regional construction-material rate book with effective dates, proof sources and a complete work-item cost engine.
6. Registry of independently approved municipality rules and certified construction-plan review workflow.
7. AI Gateway for interchangeable provider APIs with RAG of approved material references and strong tool restrictions.
8. Production cloud account, TLS and monitoring once the owner supplies their cloud provider.
