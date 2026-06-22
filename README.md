# ⚡ ElectroPaaS

A full-stack electronics B2B & B2C platform — Admin, Seller, and Customer portals.

## Project Structure

```
electropaas/
├── api/
│   └── app.py            # Flask backend (all routes)
├── frontend/
│   ├── index.html        # Login / landing page
│   ├── admin/index.html  # Admin dashboard
│   ├── seller/index.html # Seller portal
│   └── user/storefront.html  # Customer storefront
├── static/
│   ├── css/main.css      # Shared styles
│   └── js/utils.js       # Shared JS helpers
├── index.py              # Vercel entry point
├── vercel.json           # Vercel routing config
├── requirements.txt
└── README.md
```

## Roles & Features

### 🛠️ Admin
- Login: `admin` / `admin123` (change after first login)
- Add, edit, remove products (name, description, category, price, bulk price, qty)
- Add/edit/remove sellers — assign username & password
- View all seller orders, mark as **Delivered**
- Full **Billbook**: due/paid entries per seller, payment history, balance summary
- Real-time **Notifications** from sellers when they submit orders

### 🏪 Seller
- Login with admin-assigned credentials
- Browse full product catalog with bulk prices
- Add products to cart with quantity picker
- Submit bulk **Order Request** to admin with notes
- View all past orders and delivery status
- Personal **Billbook**: see what's due, paid, and outstanding balance

### 🛒 Customer (Normal User)
- Register with email & password
- Browse storefront — search, filter by category, sort by price
- View product details, add to cart
- Place orders with delivery address
- View order history

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt


## Default Credentials

| Role  | Username | Password   |
|-------|----------|------------|
| Admin | admin    | admin123   |
| Seller | (set by admin) | (set by admin) |
| User  | (register with email) | — |

**Change the admin password after your first login!**
