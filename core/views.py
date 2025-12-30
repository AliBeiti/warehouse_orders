from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, Http404, HttpResponseNotAllowed, JsonResponse
from .models import Category, Product, Order, OrderItem
from .telegram_utils import send_order_csv_via_telegram
from decimal import Decimal
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

from io import BytesIO
from .pdf_utils import build_full_picking_pdf, send_order_picking_pdf_to_telegram, build_order_receipt_pdf, send_order_receipt_pdf_to_telegram

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import csv
import io


def generate_order_csv(order):
    """
    Return CSV text for a single order in warehouse pick order.

    Columns:
        RowNumber ; PickOrder ; ProductName ; ProductCode ; Quantity
    """
    # Get items already sorted by product picking order (and name as fallback)
    ordered_items = (
        order.items
        .select_related("product")
        .order_by("product__pick_order", "product__name")
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')

    # Header row
    writer.writerow(["SatırNo", "RafSırası", "ÜrünAdı", "ÜrünKodu", "Adet"])
    #writer.writerow(["RowNumber", "PickOrder", "ProductName", "ProductCode", "Quantity"])

    # Data rows
    for idx, item in enumerate(ordered_items, start=1):
        p = item.product
        writer.writerow([
            idx,                 # RowNumber
            p.pick_order,        # PickOrder
            p.name,              # ProductName
            p.code or "",        # ProductCode
            item.quantity,       # Quantity
        ])

    csv_content = output.getvalue()
    output.close()
    return csv_content


def customer_info(request):
    """Step 1: Collect customer information"""
    
    if request.method == "POST":
        # Validate customer info
        customer_name = request.POST.get("customer_name", "").strip()
        customer_phone = request.POST.get("customer_phone", "").strip()
        customer_email = request.POST.get("customer_email", "").strip()
        customer_note = request.POST.get("customer_note", "").strip()
        
        errors = []
        if not customer_name:
            errors.append("İsim alanı zorunludur.")
        if not customer_phone:
            errors.append("Telefon alanı zorunludur.")
        
        if errors:
            return render(request, "customer_info.html", {
                "error_list": errors,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "customer_email": customer_email,
                "customer_note": customer_note,
            })
        
        # Save to session
        request.session["customer_name"] = customer_name
        request.session["customer_phone"] = customer_phone
        request.session["customer_email"] = customer_email
        request.session["customer_note"] = customer_note
        
        # Redirect to product selection
        return redirect("order_form")
    
    # GET request - show form with saved data
    return render(request, "customer_info.html", {
        "customer_name": request.session.get("customer_name", ""),
        "customer_phone": request.session.get("customer_phone", ""),
        "customer_email": request.session.get("customer_email", ""),
        "customer_note": request.session.get("customer_note", ""),
    })


def order_form(request):
    # Check if customer info exists in session - if not, redirect to step 1
    if not request.session.get("customer_name"):
        return redirect("customer_info")
    
    # All active products (used to read quantities from POST)
    products = Product.objects.filter(is_active=True)

    # Main categories (tabs): parent is NULL
    main_categories = (
        Category.objects
        .filter(parent__isnull=True)
        .order_by("display_order", "name")
        .prefetch_related("subcategories__products")
    )

    if request.method == "POST":
        # 1) Get customer info from SESSION (not POST anymore)
        customer_name = request.session.get("customer_name")
        customer_phone = request.session.get("customer_phone")
        customer_email = request.session.get("customer_email", "")
        customer_note = request.session.get("customer_note", "")

        errors = []

        # 2) Read products and quantities
        selected_items = []

        for p in products:
            field_name = f"qty_{p.id}"
            qty_raw = request.POST.get(field_name)

            try:
                qty = int(qty_raw) if qty_raw is not None else 0
            except ValueError:
                qty = 0

            if qty > 0:
                selected_items.append({
                    "product": p,
                    "quantity": qty,
                })

        if not selected_items:
            errors.append("Lütfen en az bir ürün seçiniz.")

        # if there are errors, re-render form with messages
        if errors:
            return render(request, "order_form.html", {
                "main_categories": main_categories,
                "error_list": errors,
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

        return redirect("order_success")

    # GET request - show products form with customer info from session
    return render(request, "order_form.html", {
        "main_categories": main_categories,
        "customer_name": request.session.get("customer_name"),
        "customer_phone": request.session.get("customer_phone"),
        "customer_email": request.session.get("customer_email"),
    })


def get_picking_items(order):
    return (
        order.items
        .select_related("product")
        .filter(quantity__gt=0)  # IMPORTANT: exclude deleted/zero lines
        .order_by("product__pick_order", "product__name")
    )

def order_success(request):
    order_id = request.session.get("last_order_id")
    if not order_id:
        # no recent order in session
        return redirect("order_form")

    try:
        order = Order.objects.prefetch_related("items__product").get(id=order_id)
    except Order.DoesNotExist:
        return redirect("order_form")

    # Build display lines sorted by warehouse pick order
    raw_items = list(order.items.select_related("product").all())

    lines = []
    total = Decimal("0.00")

    for oi in sorted(raw_items, key=lambda i: i.product.pick_order):
        product = oi.product

        # unit_price = discounted price if available, otherwise base price, otherwise 0
        if product.final_price is not None:
            unit_price = product.final_price
        elif product.price is not None:
            unit_price = product.price
        else:
            unit_price = Decimal("0.00")

        line_total = unit_price * oi.quantity
        total += line_total

        lines.append({
            "order_item": oi,       # <-- IMPORTANT: we keep the OrderItem here
            "product": product,
            "quantity": oi.quantity,
            "unit_price": unit_price,
            "line_total": line_total,
        })

    context = {
        "order": order,
        "items": lines,
        "total": total,
    }
    return render(request, "order_success.html", context)

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

    # --- NEW: update item quantities from the summary form ---
    for item in order.items.all():
        field_name = f"qty_{item.id}"  # matches name="qty_{{ line.order_item.id }}"
        if field_name not in request.POST:
            continue

        raw = request.POST.get(field_name)
        try:
            new_qty = int(raw)
        except (TypeError, ValueError):
            # Ignore invalid values and keep the old quantity
            continue

        if new_qty <= 0:
            # Quantity 0 (or negative) -> remove this item from the order
            item.quantity = 0
            item.delete()
            continue

        if new_qty != item.quantity:
            item.quantity = new_qty
            item.save()

    # If all items were removed, there is nothing to confirm
    if not order.items.exists():
        # You can change this behavior if you want
        return redirect("order_form")

    # Generate CSV and send via Telegram with UPDATED items
    csv_content = generate_order_csv(order)
    send_order_csv_via_telegram(order, csv_content)
    
    # Mark as confirmed
    order.is_confirmed = True
    order.save()

    # Send picking PDF after confirming (uses updated order)
    # send_order_picking_pdf_to_telegram(order)
    pdf_content = build_full_picking_pdf(order)
    send_order_picking_pdf_to_telegram(order, pdf_content)

    receipt_pdf = build_order_receipt_pdf(order)
    send_order_receipt_pdf_to_telegram(order, receipt_pdf)
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


#@login_required  
def order_receipt_pdf(request, order_id):
    """
    View wrapper: generate and return the order receipt PDF.
    """
    order = get_object_or_404(Order, pk=order_id)

    if not order.is_confirmed:
        raise Http404("Bu sipariş için fiş henüz mevcut değil (onaylanmamış).")

    pdf_bytes = build_order_receipt_pdf(order)

    filename = f"order_{order.id}_fis.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response

@login_required  
def order_picking_pdf(request, order_id):
    """
    Return the picking PDF for a given order as an HTTP response,
    so you can open it in the browser for testing or download it.
    """
    order = get_object_or_404(Order, pk=order_id)

    if not order.is_confirmed:
        raise Http404("Picking PDF is only available for confirmed orders.")

    pdf_bytes = build_full_picking_pdf(order)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="order_{order.id}_picking.pdf"'
    )
    return response



def check_print_token(request):
    token = request.headers.get("X-PRINT-TOKEN")
    if not token or token != settings.PRINT_API_TOKEN:
        return False
    return True

def orders_to_print(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    if not check_print_token(request):
        return HttpResponseForbidden("Forbidden")

    orders = (
        Order.objects
        .filter(is_confirmed=True, printed=False)
        .order_by("created_at")[:20]
    )

    data = []
    for o in orders:
        data.append({
            "id": o.id,
            "created_at": o.created_at.isoformat(),
            # Optional: include fields you want on the print agent (for logging)
            # "customer_name": o.customer_name,
            # ...
        })

    return JsonResponse(data, safe=False)


@csrf_exempt
def order_picking_pdf_for_print(request, order_id):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    if not check_print_token(request):
        return HttpResponseForbidden("Forbidden")

    try:
        order = Order.objects.get(id=order_id, is_confirmed=True)
    except Order.DoesNotExist:
        return HttpResponse(status=404)

    pdf_bytes = build_order_receipt_pdf(order)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    # filename is not so important for the script, but nice to have:
    response["Content-Disposition"] = f'inline; filename="picking_order_{order.id}.pdf"'
    return response

@csrf_exempt
def mark_order_printed(request, order_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if not check_print_token(request):
        return HttpResponseForbidden("Forbidden")

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)

    order.printed = True
    order.printed_at = timezone.now()
    order.save(update_fields=["printed", "printed_at"])

    return JsonResponse({"status": "ok", "order_id": order.id})