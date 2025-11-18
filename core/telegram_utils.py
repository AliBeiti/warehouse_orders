import requests
from django.conf import settings


def send_order_csv_via_telegram(order, csv_content: str):
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        # No config set — you may want to log this or skip silently
        return

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    files = {
        "document": (f"order_{order.id}.csv", csv_content.encode("utf-8"), "text/csv")
    }
    data = {
        "chat_id": chat_id,
        "caption": f"New order #{order.id} from {order.customer_name}",
    }

    try:
        requests.post(url, data=data, files=files, timeout=10)
    except Exception:
        # In production you'd log the error; here we just ignore failures
        pass
