# Hlophe Online Ordering System

A Django-based online ordering and order management system developed for Hlophe.

The platform allows customers to place orders online while also supporting walk-in customers through a staff-managed counter ordering system.

## Features

### Customer Online Ordering
- Browse available menu items
- Select meat and fixed-price items
- Enter customer name and WhatsApp/contact number
- Choose order type
- Add special instructions
- Receive an order reference
- Track order progress

### Staff Dashboard
- Secure staff login
- View active customer orders
- Distinguish between Online and Counter orders
- Create walk-in Counter Orders
- Assign a Braai Master
- Update order status
- Record final order total
- Mark Counter Orders as Paid or Payment Pending
- View completed and cancelled order history

### Order Workflow

Orders can progress through:

- Order Received
- Preparing Order
- Braaiing
- Ready for Collection
- Collected
- Cancelled

### EdVance Management
- Secure owner/management portal
- Monitor completed orders
- Track platform fees
- R15 platform fee per completed order
- View paid and outstanding settlements
- Monthly settlement tracking

## Technology

- Python
- Django
- PostgreSQL
- SQLite for local development
- HTML
- CSS
- WhiteNoise
- Gunicorn
- Railway

## Deployment

The application is configured for deployment on Railway with PostgreSQL.

## Developed By

EdVance Tech (Pty) Ltd.