import time
import os
import requests

BASE_URL = "https://dona-interlobular-tunefully.ngrok-free.dev"  # change to real domain
PRINT_API_TOKEN = "SECRET1234567890987654321"

HEADERS = {
    "X-PRINT-TOKEN": PRINT_API_TOKEN
}

CHECK_INTERVAL_SECONDS = 30  # how often to poll the server


def fetch_orders_to_print():
    resp = requests.get(f"{BASE_URL}/api/orders-to-print/", headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def download_picking_pdf(order_id):
    resp = requests.get(
        f"{BASE_URL}/api/orders/{order_id}/picking-pdf/",
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    filename = f"picking_order_{order_id}.pdf"
    with open(filename, "wb") as f:
        f.write(resp.content)
    return filename


def print_pdf(filename):
    """
    Windows-only: sends the PDF to the default printer.
    Make sure the default app for .pdf supports the 'print' verb.
    """
    print(f"Sending {filename} to printer...")
    os.startfile(filename, "print")


def mark_order_printed(order_id):
    resp = requests.post(
        f"{BASE_URL}/api/orders/{order_id}/mark-printed/",
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()


def main_loop():
    print("Print agent started. Press Ctrl+C to stop.")
    while True:
        try:
            orders = fetch_orders_to_print()
            if orders:
                print(f"Found {len(orders)} order(s) to print.")
            for order in orders:
                order_id = order["id"]
                try:
                    print(f"Processing order {order_id}...")
                    pdf_file = download_picking_pdf(order_id)
                    print_pdf(pdf_file)
                    # optional: wait a little between print and mark
                    time.sleep(2)
                    mark_order_printed(order_id)
                    print(f"Order {order_id} marked as printed.")
                except Exception as e:
                    print(f"Error with order {order_id}: {e}")
        except Exception as e:
            print("Error communicating with server:", e)

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main_loop()

