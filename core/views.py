from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from .models import Category, Product, Order, OrderItem
from .telegram_utils import send_order_csv_via_telegram

import csv
import io


def generate_order_csv(order):
    """Return CSV text for a single order in warehouse pick order."""
    # Build items list sorted by pick_order
    items = []
    for item in order.items.select_related("product").all():
        items.append({
            "product": item.product,
            "quantity": item.quantity,
        })

    items.sort(key=lambda x: (x["product"].pick_order, x["product"].name))

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["PickOrder", "ProductName", "ProductCode", "Quantity", "Unit"])

    for item in items:
        p = item["product"]
        writer.writerow([
            p.pick_order,
            p.name,
            p.code or "",
            item["quantity"],
            p.unit or "",
        ])

    csv_content = output.getvalue()
    output.close()
    return csv_content

# Create your views here.
def order_form(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all().order_by("display_order", "name")

    if request.method == "POST":
        # 1) Read customer info
        customer_name = request.POST.get("customer_name", "").strip()
        customer_phone = request.POST.get("customer_phone", "").strip()
        customer_email = request.POST.get("customer_email", "").strip()
        customer_note = request.POST.get("customer_note", "").strip()

        errors = []

        if not customer_name:
            errors.append("Name is required.")

        # 2) Read products and quantities
        selected_items = []

        for p in products:
            field_name = f"qty_{p.id}"
            qty_raw = request.POST.get(field_name)

            try:
                qty = int(qty_raw)
            except (TypeError, ValueError):
                qty = 0

            if qty > 0:
                selected_items.append({"product": p, "quantity": qty})

        if not selected_items:
            errors.append("Please select at least one product.")

        # If any errors, re-render form with messages and previously entered customer info
        if errors:
            return render(request, "order_form.html", {
                "categories": categories,
                "error_list": errors,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "customer_email": customer_email,
                "customer_note": customer_note,
            })

        # 3) Create Order
        order = Order.objects.create(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            customer_note=customer_note,
        )

        # 4) Create OrderItems
        for item in selected_items:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["quantity"],
            )

        # 5) Store order id in session for success / CSV
        request.session["last_order_id"] = order.id
        # optional: clear old session cart
        request.session.pop("order_items", None)

        return redirect("order_success")

    # GET request
    return render(request, "order_form.html", {"categories": categories})

def order_success(request):
    order_id = request.session.get("last_order_id")
    if not order_id:
        # no recent order in session
        return redirect("order_form")

    try:
        order = Order.objects.prefetch_related(
            "items__product"
        ).get(id=order_id)
    except Order.DoesNotExist:
        return redirect("order_form")

    # Build items list sorted by warehouse order
    items = []
    for item in order.items.all():
        items.append({
            "product": item.product,
            "quantity": item.quantity,
        })

    items.sort(key=lambda x: (x["product"].pick_order, x["product"].name))

    return render(request, "order_success.html", {
        "order": order,
        "items": items,
    })

def order_confirm(request):
    if request.method != "POST":
        return redirect("order_form")

    order_id = request.session.get("last_order_id")
    if not order_id:
        return redirect("order_form")

    try:
        order = Order.objects.prefetch_related("items__product").get(id=order_id)
    except Order.DoesNotExist:
        return redirect("order_form")

    # If already confirmed, just show final page
    if order.is_confirmed:
        return render(request, "order_confirmed.html", {"order": order})

    # Generate CSV and send via Telegram
    csv_content = generate_order_csv(order)
    send_order_csv_via_telegram(order, csv_content)

    # Mark as confirmed
    order.is_confirmed = True
    order.save()

    # Optionally clear last_order_id from session (or keep it, up to you)
    # request.session.pop("last_order_id", None)

    return render(request, "order_confirmed.html", {"order": order})

   
def order_csv_admin(request, order_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden("Not allowed")

    try:
        order = Order.objects.prefetch_related("items__product").get(id=order_id)
    except Order.DoesNotExist:
        return HttpResponse("Order not found", status=404)

    csv_content = generate_order_csv(order)
    filename = f"order_{order.id}.csv"

    response = HttpResponse(csv_content, content_type="text/csv")
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
