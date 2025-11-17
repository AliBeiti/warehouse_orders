from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Category, Product, Order, OrderItem

import csv
import io

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


def order_download_csv(request):
    order_id = request.session.get("last_order_id")
    if not order_id:
        return redirect("order_form")

    try:
        order = Order.objects.prefetch_related("items__product").get(id=order_id)
    except Order.DoesNotExist:
        return redirect("order_form")

    # Build items list sorted by warehouse pick_order
    items = []
    for item in order.items.all():
        items.append({
            "product": item.product,
            "quantity": item.quantity,
        })

    items.sort(key=lambda x: (x["product"].pick_order, x["product"].name))

    # Create CSV in memory
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

    filename = f"order_{order.id}.csv"
    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
