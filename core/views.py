from django.shortcuts import render, redirect
from .models import Product

# Create your views here.
def order_form(request):
    products = Product.objects.filter(is_active=True).order_by('pick_order', 'name')

    if request.method == "POST":
        selected_items = []

        for p in products:
            field_name = f"qty_{p.id}"
            qty_raw = request.POST.get(field_name)

            try:
                qty = int(qty_raw)
            except:
                qty = 0

            if qty > 0:
                selected_items.append({
                    "product": p,
                    "quantity": qty,
                })

        if not selected_items:
            # No items selected → return page with error
            return render(request, 'order_form.html', {
                "products": products,
                "error": "Please select at least one product.",
            })

        # Save selected_items in session (temporary storage)
        request.session['order_items'] = [
            {"id": item["product"].id, "quantity": item["quantity"]}
            for item in selected_items
        ]

        return redirect("order_success")

    return render(request, 'order_form.html', {"products": products})


def order_success(request):
    # load items from session
    saved_items = request.session.get("order_items", [])

    # fetch actual product objects
    products = Product.objects.in_bulk([item["id"] for item in saved_items])

    items = []
    for item in saved_items:
        prod = products.get(item["id"])
        if prod:
            items.append({
                "product": prod,
                "quantity": item["quantity"]
            })

    return render(request, "order_success.html", {"items": items})