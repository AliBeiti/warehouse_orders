from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, Http404
from .models import Category, Product, Order, OrderItem
from .telegram_utils import send_order_csv_via_telegram
from decimal import Decimal
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

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
        # 1) Read customer info
        customer_name = request.POST.get("customer_name", "").strip()
        customer_phone = request.POST.get("customer_phone", "").strip()
        customer_email = request.POST.get("customer_email", "").strip()
        customer_note = request.POST.get("customer_note", "").strip()

        errors = []

        if not customer_name:
            errors.append("İsim alanı zorunludur.")
        if not customer_phone:
            errors.append("Telefon alanı zorunludur.")

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

        # if there are errors, re-render form with messages + customer info
        if errors:
            return render(request, "order_form.html", {
                "main_categories": main_categories,
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
        # optional: later we can put a session cart here
        # request.session["order_items"] = ...

        return redirect("order_success")

    # GET request
    return render(request, "order_form.html", {
        "main_categories": main_categories,
    })


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
            "order_item": oi,
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


#@login_required  # optional – remove if customers should access it without login
def order_receipt_pdf(request, order_id):
    """
    Generate a PDF receipt for the given order using ReportLab.
    """
    order = get_object_or_404(Order, pk=order_id)

    if not order.is_confirmed:
        raise Http404("Receipt not available for unconfirmed orders.")

    # Create a BytesIO buffer
    buffer = BytesIO()

    # Set up the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    elements = []

    # --- Header / Title ---
    title = f"Order Receipt #{order.id}"
    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Spacer(1, 12))

    # --- Order meta info ---
    meta_text = (
        f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}<br/>"
        f"Customer: {order.customer_name}"
    )
    if order.customer_phone:
        meta_text += f"<br/>Phone: {order.customer_phone}"
    if order.customer_email:
        meta_text += f"<br/>Email: {order.customer_email}"

    elements.append(Paragraph(meta_text, styles["Normal"]))
    elements.append(Spacer(1, 12))

    if order.customer_note:
        note_text = f"<b>Customer Note:</b> {order.customer_note}"
        elements.append(Paragraph(note_text, styles["Normal"]))
        elements.append(Spacer(1, 12))

    # --- Items table ---
    data = [["#", "Product", "Quantity"]]

    for i, item in enumerate(order.items.all(), start=1):
        data.append([
            str(i),
            item.product.name,
            str(item.quantity),
        ])

    table = Table(data, colWidths=[30, 300, 80])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 18))

    # --- Footer text ---
    footer_text = (
        "Thank you for your purchase.<br/>"
        "This receipt was generated automatically and is valid without signature."
    )
    elements.append(Paragraph(footer_text, styles["Normal"]))

    # Build the PDF
    doc.build(elements)

    # Get the PDF value
    pdf_value = buffer.getvalue()
    buffer.close()

    # Return as response
    filename = f"order_{order.id}_receipt.pdf"
    response = HttpResponse(pdf_value, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response