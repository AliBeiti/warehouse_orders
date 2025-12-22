# Warehouse Orders System

Master Best Cosmetics order management and warehouse picking system.

## Features
- Customer order placement with review/edit
- Warehouse picking list generation (PDF)
- Customer receipt generation (PDF)
- Telegram notifications for new orders
- Print queue API for automated printing

## Setup Instructions

### 1. Clone and Setup
```bash
git clone <repository-url>
cd warehouse_orders
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your actual values
```

### 3. Initialize Database
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run Development Server
```bash
python manage.py runserver
```

Visit: http://localhost:8000/order/

## Environment Variables

Required in `.env`:
- `SECRET_KEY` - Django secret key
- `DEBUG` - True for development, False for production
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `TELEGRAM_CHAT_ID` - Your Telegram channel/chat ID
- `PRINT_API_TOKEN` - Secure token for print API
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts

## API Endpoints

### Print Queue API (requires X-PRINT-TOKEN header)
- `GET /api/orders-to-print/` - Get unprinted orders
- `GET /api/orders/<id>/picking-pdf/` - Download PDF
- `POST /api/orders/<id>/mark-printed/` - Mark as printed

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Use PostgreSQL instead of SQLite
3. Run `python manage.py collectstatic`
4. Use Gunicorn + Nginx
5. Set up SSL certificate

## Support
Contact: [alibeity77@gmail.com]