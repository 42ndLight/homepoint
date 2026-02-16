---
name: POS System 4-Week Implementation Plan
overview: A comprehensive 4-week implementation plan for building a hardware store POS system with authentication, product catalog, barcode scanning, M-Pesa payments, eTIMS receipts, and admin dashboard.
todos: []
---

# POS System 4-Week Implementation Plan

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 + Vite)                  │
├─────────────────────────────────────────────────────────────┤
│  Auth Store (Pinia) → API Service → Django REST API        │
│  Cart Store (Pinia) → Local Storage + Dexie.js (offline)   │
│  Product Search → Fuse.js (fuzzy) + QuaggaJS (barcode)     │
│  Payment Flow → M-Pesa STK Push → eTIMS Receipt            │
│  Admin Dashboard → Chart.js (analytics)                     │
└─────────────────────────────────────────────────────────────┘
```

## Week 1: Setup & Authentication

### Day 1: Project Foundation & API Service Layer

**Deliverables:**

- API service layer with axios/fetch wrapper
- Environment configuration for API base URL
- Error handling middleware
- HTTP interceptors for JWT token injection

**Technical Implementation:**

- Create `src/services/api.js` with base axios instance
- Configure request/response interceptors for JWT tokens
- Create `src/config/env.js` for API endpoints
- Set up error handling for 401/403/500 responses

**Files to Create:**

- `src/services/api.js`
- `src/config/env.js`
- `src/utils/errorHandler.js`

### Day 2: Complete Auth Store & Login UI

**Deliverables:**

- Enhanced Pinia auth store with user data persistence
- Complete login view with error handling
- JWT token refresh logic
- User role extraction from JWT payload

**Technical Implementation:**

- Update `src/stores/auth.js`:
  - Add `user` state with role, permissions
  - Add `refreshToken()` method
  - Add `checkAuth()` method to validate token on app init
  - Persist user data to localStorage
- Complete `src/views/auth/LoginView.vue`:
  - Connect to real API endpoint (`/users/auth/token/`)
  - Handle JWT decode to extract user role
  - Display error messages using PrimeVue Toast
  - Add loading states

**Files to Modify:**

- `src/stores/auth.js`
- `src/views/auth/LoginView.vue`

### Day 3: Route Guards & Protected Routes

**Deliverables:**

- Router configuration with all routes
- Route guards for authentication
- Role-based route protection (admin vs cashier)
- Redirect logic for unauthenticated users

**Technical Implementation:**

- Create `src/router/index.js` routes:
  - `/login` - LoginView
  - `/pos` - POSView (cashier role)
  - `/admin` - AdminDashboardView (admin role)
  - `/catalog` - ProductCatalogView (all authenticated)
- Implement `router.beforeEach` guard:
  - Check `authStore.isAuthenticated()`
  - Check user role for admin routes
  - Redirect to `/login` if not authenticated
  - Redirect to role-appropriate dashboard after login

**Files to Create:**

- `src/router/guards.js`
- `src/router/index.js` (update)

### Day 4: Logout & User Profile

**Deliverables:**

- Logout functionality
- User profile display component
- Token blacklist integration (backend logout endpoint)

**Technical Implementation:**

- Add logout button to App.vue or layout
- Call `/users/auth/logout/` endpoint to blacklist token
- Clear auth store and localStorage
- Create `src/components/UserProfile.vue` component
- Add profile route if needed

**Files to Create:**

- `src/components/UserProfile.vue`
- `src/views/auth/LogoutView.vue` (optional)

### Day 5: Testing & Refinement

**Deliverables:**

- Test complete auth flow (login → protected route → logout)
- Fix any token refresh issues
- Test role-based access control
- Document API endpoints used

**Testing Checklist:**

- Login with valid credentials
- Login with invalid credentials
- Access protected route without auth (should redirect)
- Access admin route as cashier (should redirect)
- Token refresh on 401 response
- Logout clears all data

---

## Week 2: Catalog & Search

### Day 6: Dexie.js Setup & Product Schema

**Deliverables:**

- Dexie database schema for products, variants, inventory
- Database initialization service
- IndexedDB setup for offline storage

**Technical Implementation:**

- Create `src/db/index.js`:
  - Define Dexie database: `homepointDB`
  - Tables: `products`, `variants`, `inventory`, `categories`
  - Indexes on `sku`, `name`, `category_id`
- Create `src/services/dbService.js`:
  - `syncProducts()` - Fetch from API and store in Dexie
  - `getProducts()` - Query from Dexie
  - `searchProducts(query)` - Local search

**Files to Create:**

- `src/db/index.js`
- `src/services/dbService.js`

### Day 7: Product Catalog Grid Component

**Deliverables:**

- Responsive product grid using PrimeVue DataView
- Product card component with image, name, price, stock
- Category filtering
- Pagination

**Technical Implementation:**

- Create `src/views/catalog/ProductCatalogView.vue`:
  - Use PrimeVue `DataView` with grid layout
  - Fetch products from Dexie (fallback to API)
  - Display product cards with:
    - Product image (placeholder if none)
    - Product name and category
    - Variant prices (show min-max range)
    - Stock status badge
- Create `src/components/product/ProductCard.vue`
- Add category filter dropdown

**Files to Create:**

- `src/views/catalog/ProductCatalogView.vue`
- `src/components/product/ProductCard.vue`
- `src/components/product/CategoryFilter.vue`

### Day 8: Fuse.js Fuzzy Search Integration

**Deliverables:**

- Search input component with fuzzy matching
- Real-time search results
- Search highlighting in results

**Technical Implementation:**

- Create `src/composables/useProductSearch.js`:
  - Initialize Fuse.js with products array
  - Configure search keys: `['name', 'description', 'sku', 'category.name']`
  - Set threshold: 0.3 (fuzzy matching)
- Create `src/components/search/ProductSearch.vue`:
  - Debounced input (300ms)
  - Display search results dropdown
  - Highlight matching text
  - "Add to Cart" button on each result

**Files to Create:**

- `src/composables/useProductSearch.js`
- `src/components/search/ProductSearch.vue`

### Day 9: Barcode Scanner Integration (QuaggaJS)

**Deliverables:**

- Barcode scanner component
- Camera access and scanning UI
- Auto-add to cart on successful scan

**Technical Implementation:**

- Create `src/components/barcode/BarcodeScanner.vue`:
  - Initialize QuaggaJS with camera stream
  - Configure for EAN/UPC/Code128 formats
  - On successful scan:
    - Lookup product by SKU/barcode in Dexie
    - Emit event or call cart store
    - Show success toast
  - Add "Scan Barcode" button in POS view
- Handle camera permissions and errors

**Files to Create:**

- `src/components/barcode/BarcodeScanner.vue`
- `src/composables/useBarcodeScanner.js`

### Day 10: Inventory Sync & Offline Support

**Deliverables:**

- Background sync service
- Sync status indicator
- Conflict resolution for offline edits

**Technical Implementation:**

- Create `src/services/syncService.js`:
  - `syncAll()` - Fetch all products/variants/inventory from `/products/`
  - Store in Dexie with timestamps
  - Run on app startup and every 5 minutes
- Add sync status to UI (online/offline indicator)
- Handle sync errors gracefully
- Create `src/composables/useSync.js` for reactive sync state

**Files to Create:**

- `src/services/syncService.js`
- `src/composables/useSync.js`

---

## Week 3: POS & Payments

### Day 11: Cart Store (Pinia) Implementation

**Deliverables:**

- Complete cart store with add/remove/update logic
- Quantity handling for decimal units (meters, kg)
- VAT calculation (16%)
- Cart persistence to localStorage

**Technical Implementation:**

- Create `src/stores/cart.js`:
  - State: `items[]`, `subtotal`, `vat`, `total`
  - Actions:
    - `addItem(variant, quantity)` - Add or update quantity
    - `removeItem(variantId)`
    - `updateQuantity(variantId, quantity)`
    - `clearCart()`
  - Getters:
    - `itemCount` - Total items
    - `subtotal` - Sum of (price × quantity)
    - `vat` - subtotal × 0.16
    - `total` - subtotal + vat
  - Persist to localStorage on changes

**Files to Create:**

- `src/stores/cart.js`

### Day 12: POS Cart UI Component

**Deliverables:**

- Cart sidebar/panel component
- Item list with quantity controls
- Price breakdown display
- Checkout button

**Technical Implementation:**

- Create `src/views/pos/POSView.vue`:
  - Split layout: Product search/grid (left) + Cart (right)
  - Use PrimeVue `Sidebar` or `Panel` for cart
- Create `src/components/cart/CartPanel.vue`:
  - Display cart items with:
    - Product name, variant SKU
    - Quantity input (supports decimals)
    - Unit price and line total
    - Remove button
  - Show subtotal, VAT (16%), total
  - "Checkout" button

**Files to Create:**

- `src/views/pos/POSView.vue`
- `src/components/cart/CartPanel.vue`
- `src/components/cart/CartItem.vue`

### Day 13: Order Creation & Backend Integration

**Deliverables:**

- Order creation API integration
- Order store (Pinia) for order management
- Order confirmation flow

**Technical Implementation:**

- Create `src/stores/order.js`:
  - `createOrder(cartItems, customerPhone, deliveryLocation)`
  - Call `/orders/orders/` POST endpoint
  - Handle order response and store order ID
- Update cart store to clear after successful order
- Create `src/components/checkout/CheckoutForm.vue`:
  - Customer phone input
  - Delivery location input
  - Payment method selection (M-Pesa, Cash)
  - Submit order button

**Files to Create:**

- `src/stores/order.js`
- `src/components/checkout/CheckoutForm.vue`

### Day 14: M-Pesa STK Push Integration (Backend)

**Deliverables:**

- M-Pesa payment model
- STK Push endpoint
- Payment status tracking

**Technical Implementation:**

- Update `payments/models.py`:
  - `Payment` model with:
    - `order` (ForeignKey to Order)
    - `payment_method` (choices: 'mpesa', 'cash')
    - `mpesa_receipt_number`
    - `amount`
    - `status` (pending, completed, failed)
    - `created_at`, `updated_at`
- Create `payments/views.py`:
  - `STKPushView` - Initiate STK Push
  - `PaymentCallbackView` - Handle M-Pesa callback
  - Use `requests` library to call M-Pesa API
- Add M-Pesa credentials to Django settings (env vars)

**Files to Modify:**

- `payments/models.py`
- `payments/views.py`
- `payments/urls.py` (create if needed)
- `homepointBackend/settings.py` (add M-Pesa config)

### Day 15: M-Pesa STK Push Integration (Frontend)

**Deliverables:**

- STK Push trigger from checkout
- Payment status polling
- "Waiting for PIN" loading state

**Technical Implementation:**

- Create `src/services/paymentService.js`:
  - `initiateSTKPush(orderId, phoneNumber, amount)`
  - `pollPaymentStatus(paymentId)` - Poll every 2 seconds
  - `getPaymentStatus(paymentId)`
- Update `CheckoutForm.vue`:
  - On M-Pesa selection, call STK Push
  - Show loading overlay: "Waiting for customer to enter PIN..."
  - Poll payment status until completed/failed
  - On success, redirect to receipt
  - On failure, show error message

**Files to Create:**

- `src/services/paymentService.js`
- `src/components/payment/STKPushLoader.vue`

---

## Week 4: eTIMS & Dashboard

### Day 16: eTIMS Receipt Format & QR Code

**Deliverables:**

- Receipt component with KRA-compliant format
- QR code generation for invoice
- Print stylesheet (@media print)

**Technical Implementation:**

- Install `qrcode` library (or use API)
- Create `src/components/receipt/ETIMSReceipt.vue`:
  - Header: Store name, address, TIN
  - Order details: Order #, date, items table
  - Totals: Subtotal, VAT (16%), Total
  - Footer: QR code (encoded invoice data), thank you message
- Create `src/assets/css/print.css`:
  - `@media print` styles
  - Hide navigation, show only receipt
  - Page break controls
  - Receipt width (80mm for thermal printers)

**Files to Create:**

- `src/components/receipt/ETIMSReceipt.vue`
- `src/assets/css/print.css`
- `src/views/receipt/ReceiptView.vue`

### Day 17: Print Preview & Receipt Generation

**Deliverables:**

- Print preview modal
- Print functionality
- Receipt data formatting

**Technical Implementation:**

- Create `src/views/receipt/ReceiptView.vue`:
  - Fetch order data from API
  - Display ETIMSReceipt component
  - "Print" button triggers `window.print()`
  - "Download PDF" option (using html2pdf.js if needed)
- Format receipt data:
  - Invoice number: `INV-{order.id}-{timestamp}`
  - QR code data: JSON with order ID, total, TIN, date

**Files to Create:**

- `src/views/receipt/ReceiptView.vue`
- `src/utils/receiptFormatter.js`

### Day 18: Admin Dashboard - Sales Reports

**Deliverables:**

- Daily/weekly/monthly revenue charts
- Sales summary cards
- Date range filters

**Technical Implementation:**

- Create `src/views/admin/AdminDashboardView.vue`
- Create `src/components/admin/SalesChart.vue`:
  - Use Chart.js with PrimeVue Charts wrapper
  - Line chart for daily revenue
  - Bar chart for product sales
- Create API endpoint `/orders/analytics/`:
  - Return daily sales data
  - Filter by date range
- Create `src/services/analyticsService.js`:
  - `getSalesData(startDate, endDate)`
  - `getTopProducts(limit)`

**Files to Create:**

- `src/views/admin/AdminDashboardView.vue`
- `src/components/admin/SalesChart.vue`
- `src/components/admin/SalesSummary.vue`
- `src/services/analyticsService.js`

### Day 19: Stock Management & Transaction Logs

**Deliverables:**

- Stock update table (admin only)
- Transaction history table
- Re-print receipt functionality

**Technical Implementation:**

- Create `src/views/admin/StockManagementView.vue`:
  - DataTable with products/variants
  - Editable quantity column
  - Bulk update functionality
  - Call `/products/inventory/{id}/` PATCH endpoint
- Create `src/views/admin/TransactionLogsView.vue`:
  - DataTable with orders
  - Columns: Order #, Date, Customer, Amount, Status
  - Search/filter by date, customer phone
  - "Re-print Receipt" button → opens ReceiptView

**Files to Create:**

- `src/views/admin/StockManagementView.vue`
- `src/views/admin/TransactionLogsView.vue`

### Day 20: PWA Configuration & Final Testing

**Deliverables:**

- PWA manifest configuration
- Service worker for offline support
- Final integration testing
- Bug fixes

**Technical Implementation:**

- Update `vite.config.js` PWA plugin:
  - Configure manifest with app name, icons
  - Set up service worker for offline caching
  - Cache API responses (products, categories)
- Test offline functionality:
  - Product search works offline
  - Cart persists offline
  - Orders queue for sync when online
- Final testing checklist:
  - Complete order flow (catalog → cart → payment → receipt)
  - Admin dashboard loads correctly
  - Barcode scanning works
  - Print receipt formats correctly
  - Mobile responsiveness

**Files to Modify:**

- `vite.config.js`
- `public/manifest.json` (if exists)

---

## Key Technical Decisions

### State Management

- **Pinia stores**: `auth`, `cart`, `order`
- **Local persistence**: localStorage for auth/cart, Dexie for products

### API Integration

- **Base URL**: Configured via environment variables
- **Authentication**: JWT tokens in Authorization header
- **Error handling**: Centralized in API service layer

### Offline Support

- **Dexie.js**: Local product database for instant search
- **Background sync**: Periodic sync every 5 minutes
- **Queue system**: Queue orders when offline, sync on reconnect

### Payment Flow

```
Cart → Checkout → Order Creation → M-Pesa STK Push → 
Poll Status → Payment Confirmed → Receipt Generation
```

### Receipt Format

- **KRA Compliance**: TIN, invoice number, VAT breakdown
- **QR Code**: Encoded invoice data for eTIMS validation
- **Print**: 80mm thermal printer compatible CSS

## Dependencies Summary

**Already Installed:**

- Vue 3, PrimeVue, Pinia, Vue Router
- Dexie, Fuse.js, Quagga, Chart.js
- TailwindCSS, Vite PWA plugin

**May Need to Add:**

- `axios` (if not using fetch)
- `qrcode` or `qrcodejs2` (for QR code generation)
- `html2pdf.js` (optional, for PDF download)

## Backend Endpoints Required

- `POST /users/auth/token/` - Login (exists)
- `POST /users/auth/logout/` - Logout (exists)
- `GET /products/products/` - List products (exists)
- `GET /products/variants/` - List variants (exists)
- `GET /products/inventory/` - List inventory (exists)
- `POST /orders/orders/` - Create order (exists)
- `POST /payments/stk-push/` - Initiate M-Pesa (to create)
- `GET /payments/payment/{id}/` - Get payment status (to create)
- `GET /orders/analytics/` - Sales analytics (to create)
- `PATCH /products/inventory/{id}/` - Update stock (exists)