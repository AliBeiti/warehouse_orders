from io import BytesIO
from math import ceil
import os
from decimal import Decimal
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    PageBreak,
    Spacer,
    Image
)

from .models import Product, Order
from django.conf import settings
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_PATH = os.path.join(settings.BASE_DIR, "fonts", "DejaVuSans.ttf")
pdfmetrics.registerFont(TTFont("DejaVu", FONT_PATH))
# ============================
#  LAYOUT DEFINITIONS BY CODE
# ============================

# ---------- PAGE 1 ----------
# First table: 214 codes (001–214) in a 20 x 11 grid
# IMPORTANT:
# If you have special codes like 008D, 009G, etc., change them manually in this list
# at the correct position (instead of "008", "009", ...).
PAGE1_TABLE1_CODES = [f"{i:03d}" for i in range(1, 215)]  # "001", "002", ..., "214"
PAGE1_TABLE1_CODES[7] = "008D"
PAGE1_TABLE1_CODES[8] = "009G"
PAGE1_TABLE1_CODES[9] = "010G"
PAGE1_TABLE1_CODES[10] = "011G"
PAGE1_TABLE1_CODES[14] = "015D"
PAGE1_TABLE1_CODES[15] = "016D"
PAGE1_TABLE1_CODES[16] = "017D"
PAGE1_TABLE1_CODES[17] = "018D"
PAGE1_TABLE1_CODES[18] = "019D"
PAGE1_TABLE1_CODES[19] = "020D"
PAGE1_TABLE1_CODES[20] = "021D"
PAGE1_TABLE1_CODES[39] = "040D"
PAGE1_TABLE1_CODES[40] = "041D"
PAGE1_TABLE1_CODES[41] = "042D"
PAGE1_TABLE1_CODES[60] = "061D"
PAGE1_TABLE1_CODES[61] = "062G"
PAGE1_TABLE1_CODES[62] = "063G"
PAGE1_TABLE1_CODES[76] = "077D"
PAGE1_TABLE1_CODES[80] = "081G"
PAGE1_TABLE1_CODES[81] = "082G"
PAGE1_TABLE1_CODES[82] = "083D"
PAGE1_TABLE1_CODES[83] = "084D"
PAGE1_TABLE1_CODES[104] = "105D"
PAGE1_TABLE1_CODES[117] = "118D"
PAGE1_TABLE1_CODES[118] = "119D"
PAGE1_TABLE1_CODES[125] = "126D"
PAGE1_TABLE1_CODES[139] = "140D"
PAGE1_TABLE1_CODES[144] = "145G"
PAGE1_TABLE1_CODES[145] = "146G"
PAGE1_TABLE1_CODES[146] = "147G"
PAGE1_TABLE1_CODES[158] = "159D"
PAGE1_TABLE1_CODES[159] = "160D"
PAGE1_TABLE1_CODES[160] = "161D"



# ---------- PAGE 2 ----------
# First table: CE01 – CE49 (20 columns, 3 rows; 60 cells, 49 used)
PAGE2_TABLE1_CODES = [f"CE{i:02d}" for i in range(1, 50)]

# Second table: C01 – C14 in ONE row
PAGE2_TABLE2_CODES = [f"C{i:02d}" for i in range(1, 15)]

# Third table: D01 – D30 in 2 rows, 20 columns (40 cells, 30 used)
PAGE2_TABLE3_CODES = [f"D{i:02d}" for i in range(1, 31)]


# ---------- PAGE 3 ----------
# All tables: ONE row each

# 1) P01 – P05
PAGE3_TABLE1_CODES = [f"P{i:02d}" for i in range(1, 7)]

# 2) L01 – L07
PAGE3_TABLE2_CODES = [f"L{i:02d}" for i in range(1, 8)]

# 3) R01 – R06 and R01(30) as last one
# NOTE: "R01(30)" must exactly match Product.code in your DB
PAGE3_TABLE3_CODES = [f"R{i:02d}" for i in range(1, 7)] + ["R01(30)"]

# 4) S01 – S12
PAGE3_TABLE4_CODES = [f"S{i:02d}" for i in range(1, 13)]

# 5) B01 – B14
PAGE3_TABLE5_CODES = [f"B{i:02d}" for i in range(1, 15)]

# 6) PO01 – PO05
PAGE3_TABLE6_CODES = [f"PO{i:02d}" for i in range(1, 6)]

# 7) NB01 – NB06
PAGE3_TABLE7_CODES = [f"NB{i:02d}" for i in range(1, 7)]


class TableLayout:
    def __init__(self, codes, num_cols, label=None):
        self.codes = codes
        self.num_cols = num_cols
        self.label=label


# PAGES: list of pages, each page = list of TableLayout
PAGES = [
    # PAGE 1
    [
        TableLayout(PAGE1_TABLE1_CODES, num_cols=20, label="GEL POLISH"),   # 20 x 11 grid (214 codes)
    ],
    # PAGE 2
    [
        TableLayout(PAGE2_TABLE1_CODES, num_cols=20, label="CAT EYES"),   # CE01–CE49 (max 20 x 3)
        TableLayout(PAGE2_TABLE2_CODES, num_cols=len(PAGE2_TABLE2_CODES), label="CANDY COLORS"),  # C01–C14 in 1 row
        TableLayout(PAGE2_TABLE3_CODES, num_cols=20, label="DISCO COLORS"),   # D01–D30 (max 2 rows, 20 cols)
        TableLayout(PAGE3_TABLE1_CODES, num_cols=len(PAGE3_TABLE1_CODES), label="PAINTING GEL"),  # P01–P05
          # L01–L07
    ],
    # PAGE 3 – all one row
    [
        TableLayout(PAGE3_TABLE2_CODES, num_cols=len(PAGE3_TABLE2_CODES), label= "LINER GEL"),
        TableLayout(PAGE3_TABLE3_CODES, num_cols=len(PAGE3_TABLE3_CODES), label="RUBBER BASE"),  # R01–R06 + R01(30)
        TableLayout(PAGE3_TABLE4_CODES, num_cols=len(PAGE3_TABLE4_CODES), label="STRUCTURE BASE"),  # S01–S12
        TableLayout(PAGE3_TABLE5_CODES, num_cols=len(PAGE3_TABLE5_CODES), label="BUILDER GEL"),  # B01–B14
        TableLayout(PAGE3_TABLE6_CODES, num_cols=len(PAGE3_TABLE6_CODES), label="POLY GEL"),  # PO01–PO05
        TableLayout(PAGE3_TABLE7_CODES, num_cols=len(PAGE3_TABLE7_CODES), label="NON STICK BUILDER GEL"),  # NB01–NB06
    ],
]


# ============================
#  PDF BUILDER
# ============================

def build_full_picking_pdf(order: Order) -> bytes:
    """
    Build a multi-page picking PDF.

    • Page 1: header + customer info + GEL POLISH grid
    • Page 2–3: category titles (CAT EYES, CANDY COLORS, etc.) + tables.

    For each code there are TWO stacked rows:
      - top row: code (001, CE25, ...)
      - bottom row: quantity from this order (blank if none)

    All rows on the same page have the SAME height, so the grid is uniform
    and tables do not flow to the next page.
    """
    buffer = BytesIO()

    page_size = landscape(A4)
    page_width, page_height = page_size
    margin = 20

    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
    )

    styles = getSampleStyleSheet()

    # Big header styles
    header_title_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Title"],
        fontName="DejaVu",
        fontSize=18,
        leading=20,
        alignment=1,  # center
        textColor=colors.HexColor("#4B2E83"),  # purple-ish
    )

    header_subtitle_style = ParagraphStyle(
        "HeaderSubtitle",
        parent=styles["Normal"],
        fontName="DejaVu",
        fontSize=11,
        leading=13,
        alignment=1,  # center
        textColor=colors.HexColor("#4B2E83"),
    )

    header_info_label_style = ParagraphStyle(
        "HeaderInfoLabel",
        parent=styles["Normal"],
        fontName="DejaVu",
        fontSize=9,
        leading=11,
        alignment=0,
    )

    header_info_value_style = ParagraphStyle(
        "HeaderInfoValue",
        parent=styles["Normal"],
        fontName="DejaVu",
        fontSize=9,
        leading=11,
        alignment=0,
    )

    # Category titles (CAT EYES, etc.)
    table_title_style = ParagraphStyle(
        "TableTitle",
        parent=styles["Heading3"],
        fontName="DejaVu",
        fontSize=12,
        leading=14,
        alignment=1,  # center
        textColor=colors.HexColor("#4B2E83"),
        spaceAfter=4,
        spaceBefore=8,
    )

    note_title_style = ParagraphStyle(
        "NoteTitle",
        parent=styles["Heading2"],
        fontName="DejaVu",
        fontSize=16,
        leading=18,
        alignment=0,  # left
        textColor=colors.HexColor("#4B2E83"),
        spaceBefore=0,
        spaceAfter=10,
    )

    note_body_style = ParagraphStyle(
        "NoteBody",
        parent=styles["Normal"],
        fontName="DejaVu",
        fontSize=10,
        leading=13,
        alignment=0,  # left
    )


    # Style for layout code (top cell)
    code_style = ParagraphStyle(
        "CodeCell",
        parent=styles["Normal"],
        fontName="DejaVu",
        fontSize=10,
        leading=10,
        alignment=1,   # center
        spaceBefore=0,
        spaceAfter=0,
    )

    # Style for quantity (bottom cell)
    qty_style = ParagraphStyle(
        "QtyCell",
        parent=styles["Normal"],
        fontName="DejaVu",
        fontSize=10,
        leading=9,
        alignment=1,   # center
        textColor=colors.darkred,
        spaceBefore=0,
        spaceAfter=0,
    )

    # 1) Map product_id -> quantity for this order
    qty_by_product_id = {
        item.product_id: item.quantity for item in order.items.all()
    }

    # 2) Map layout code -> Product via suffix of Product.code (MBKO****)
    products_by_code = {}
    for p in Product.objects.filter(is_active=True):
        if not p.code:
            continue
        raw = p.code.strip()
        if len(raw) <= 4:
            continue
        suffix = raw[4:]  # 5th char to end: "MBKO001" -> "001", "MBKOCE25" -> "CE25"
        products_by_code[suffix] = p

    elements = []

    for page_idx, page_tables in enumerate(PAGES):
        # ---------- PAGE 1 HEADER ----------
        if page_idx == 0:
            elements.append(Paragraph("SİPARİŞ LİSTESİ", header_title_style))
            elements.append(Paragraph("MASTER BEST SİPARİŞ LİSTESİ – GEL POLISH", header_subtitle_style))
            elements.append(Spacer(1, 8))

            # Customer info (Turkish)
            lines = []

            if order.customer_name:
                lines.append(f"<b>İsim Soyisim:</b> {order.customer_name}")

            if order.customer_phone:
                lines.append(f"<b>Telefon:</b> {order.customer_phone}")

            if order.customer_email:
                lines.append(f"<b>E-posta:</b> {order.customer_email}")

            lines.append(
                f"<b>Tarih:</b> {order.created_at.strftime('%d.%m.%Y')}"
            )

            info_html = "<br/>".join(lines)
            elements.append(Paragraph(info_html, header_info_value_style))
            elements.append(Spacer(1, 10))

            elements.append(Spacer(1, 4))

        # ---------- ROW HEIGHT CALC PER PAGE ----------
        # Count total physical rows (code + qty rows) on this page
        total_physical_rows_on_page = 0
        physical_rows_per_table = []

        for table_layout in page_tables:
            codes = table_layout.codes
            num_cols = table_layout.num_cols
            num_cells = len(codes)
            logical_rows = ceil(num_cells / num_cols)
            physical_rows = 2 * logical_rows
            physical_rows_per_table.append(physical_rows)
            total_physical_rows_on_page += physical_rows

        inner_width = page_width - 2 * margin

        # --- how much vertical space is available for rows on this page ---
        if page_idx == 0:
            # Page 1: big header
            header_reserved = 120
        elif page_idx == 1:
            # Page 2: some titles
            header_reserved = 40
        else:
            # Page 3: a bit less reserved so we have more room,
            # but we'll compress rows more
            header_reserved = 40

        available_height = page_height - 2 * margin - header_reserved
        if available_height < 80:
            available_height = page_height - 2 * margin - 60  # fallback

        # Compression factor:
        #  - Page 0: nice big cells
        #  - Page 1: slightly smaller
        #  - Page 2 (index 2): even smaller so all 7 tables fit
        if page_idx == 0:
            compression = 0.85
        elif page_idx == 1:
            compression = 0.75
        else:  # page_idx == 2 -> 3rd page
            compression = 0.65

        base_inner_height = available_height * compression

        # One uniform row height for EVERY row on this page
        row_height = base_inner_height / max(1, total_physical_rows_on_page)


        # ---------- BUILD TABLES ----------
        for table_idx, table_layout in enumerate(page_tables):
            codes = table_layout.codes
            num_cols = table_layout.num_cols
            num_cells = len(codes)
            logical_rows = ceil(num_cells / num_cols)
            physical_rows = 2 * logical_rows

            # Fancy category title like "CAT EYES", "CANDY COLORS", etc.
            if table_layout.label:
                elements.append(Paragraph(table_layout.label, table_title_style))

            # Build flat code/qty lists
            codes_flat = []
            qtys_flat = []

            for code in codes:
                product = products_by_code.get(code)
                if product:
                    qty = qty_by_product_id.get(product.id, 0)
                else:
                    qty = 0

                qty_text = "-" if qty == 0 else str(qty)
                codes_flat.append(Paragraph(code, code_style))
                qtys_flat.append(Paragraph(qty_text, qty_style))

            # pad to fill full grid
            total_slots = logical_rows * num_cols
            while len(codes_flat) < total_slots:
                codes_flat.append(Paragraph("", code_style))
                qtys_flat.append(Paragraph("", qty_style))

            data = []
            idx = 0
            for _ in range(logical_rows):
                code_row = []
                qty_row = []
                for _ in range(num_cols):
                    code_row.append(codes_flat[idx])
                    qty_row.append(qtys_flat[idx])
                    idx += 1
                data.append(code_row)
                data.append(qty_row)

            col_width = inner_width / num_cols

            table = Table(
                data,
                colWidths=[col_width] * num_cols,
                rowHeights=[row_height] * physical_rows,
            )
            table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ]))

            elements.append(table)
            elements.append(Spacer(1, 10))

        # Page break between pages (except last)
        if page_idx != len(PAGES) - 1:
            elements.append(PageBreak())
    if order.customer_note:
        elements.append(PageBreak())
        elements.append(Paragraph("MÜŞTERİ NOTU", note_title_style))
        elements.append(Spacer(1, 12))

        # Convert line breaks in the note to <br/> so they are respected
        note_text = order.customer_note.replace("\n", "<br/>")
        elements.append(Paragraph(note_text, note_body_style))
    doc.build(elements)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes



# ============================
#  OPTIONAL: TELEGRAM SENDER
# ============================

import requests

# Set these appropriately (env vars are better in real project)
TELEGRAM_BOT_TOKEN = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = getattr(settings, "TELEGRAM_CHAT_ID", "")

def send_order_receipt_pdf_to_telegram(order: Order, pdf_content: bytes):
    """
    Send customer receipt PDF to Telegram.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    files = {
        "document": (
            f"order_{order.id}_receipt.pdf",
            pdf_content,
            "application/pdf",
        )
    }

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": f"📄 Müşteri Fişi - Sipariş #{order.id}\n"
                   f"👤 {order.customer_name}\n"
                   f"📞 {order.customer_phone}",
    }

    try:
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()
    except Exception as e:
        # Log error but don't fail the order
        print(f"Failed to send receipt to Telegram: {e}")

def send_order_picking_pdf_to_telegram(order: Order,pdf_content):
    """
    Build the picking PDF for this order and send it as a document to Telegram.
    """
    pdf_bytes = build_full_picking_pdf(order)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    files = {
        "document": (
            f"order_{order.id}_picking.pdf",
            pdf_content,
            "application/pdf",
        )
    }

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": f"Picking PDF for Order #{order.id}",
    }

    response = requests.post(url, data=data, files=files)
    response.raise_for_status()



def build_order_receipt_pdf(order: Order) -> bytes:
    """
    Build a Turkish PDF receipt for the given order.

    Columns:
        #, Ürün, Adet, Birim Fiyatı, Satır Toplamı
    Includes:
        - Master Best header (with optional logo)
        - Customer info
        - General total at the bottom
    Returns:
        PDF bytes
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Use DejaVu if registered, otherwise fall back to Helvetica
    base_font = "DejaVu" if "DejaVu" in pdfmetrics.getRegisteredFontNames() else "Helvetica"

    header_title_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Title"],
        fontName=base_font,
        fontSize=16,
        leading=18,
        alignment=1,  # center
        textColor=colors.HexColor("#4B2E83"),
    )

    header_sub_style = ParagraphStyle(
        "HeaderSub",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=10,
        leading=12,
        alignment=1,
    )

    info_style = ParagraphStyle(
        "Info",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=9,
        leading=11,
        alignment=0,  # left
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=9,
        leading=11,
        alignment=1,  # center
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=9,
        leading=11,
        alignment=0,  # left
    )

    table_cell_right_style = ParagraphStyle(
        "TableCellRight",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=9,
        leading=11,
        alignment=2,  # right
    )

    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=8,
        leading=10,
        alignment=1,
        textColor=colors.grey,
    )

    elements = []

    # --- Optional logo + company header ---
    # Put your logo at: BASE_DIR/static/img/masterbest_logo.png
    logo_path = os.path.join(settings.BASE_DIR, "static", "img", "logo.png")
    header_table_row = []

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=60, height=60)
        header_table_row.append(logo)
    else:
        header_table_row.append("")

    header_text = [
        Paragraph("MASTER BEST", header_title_style),
        Paragraph("SİPARİŞ FİŞİ", header_sub_style),
    ]
    header_table_row.append(header_text)

    header_table = Table([header_table_row], colWidths=[70, 400])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # --- Customer info (Turkish) ---
    info_lines = []

    if order.customer_name:
        info_lines.append(f"<b>İsim Soyisim:</b> {order.customer_name}")
    if order.customer_phone:
        info_lines.append(f"<b>Telefon:</b> {order.customer_phone}")
    if order.customer_email:
        info_lines.append(f"<b>E-posta:</b> {order.customer_email}")

    info_lines.append(f"<b>Tarih:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}")

    info_html = "<br/>".join(info_lines)
    elements.append(Paragraph(info_html, info_style))
    elements.append(Spacer(1, 10))

    if order.customer_note:
        note_text = order.customer_note.replace("\n", "<br/>")
        elements.append(Paragraph(f"<b>Müşteri Notu:</b><br/>{note_text}", info_style))
        elements.append(Spacer(1, 10))

    # --- Items table with prices ---
    data = [[
        Paragraph("#", table_header_style),
        Paragraph("Ürün", table_header_style),
        Paragraph("Adet", table_header_style),
        Paragraph("Birim Fiyatı", table_header_style),
        Paragraph("Toplamı", table_header_style),
    ]]

    ara_toplam = Decimal("0.00")
    ordered_items = (
        order.items
        .select_related("product")
        .order_by("product__pick_order", "product__display_order", "product__name")
    )
    for idx, item in enumerate(ordered_items, start=1):
        product = item.product
        qty = item.quantity

        # unit price: final_price -> price -> 0
        unit_price = product.final_price or product.price or Decimal("0.00")
        line_total = (unit_price or Decimal("0.00")) * qty
        ara_toplam += line_total

        unit_price_str = f"{unit_price:.2f} ₺"
        line_total_str = f"{line_total:.2f} ₺"

        data.append([
            Paragraph(str(idx), table_cell_style),
            Paragraph(product.name, table_cell_style),
            Paragraph(str(qty), table_cell_right_style),
            Paragraph(unit_price_str, table_cell_right_style),
            Paragraph(line_total_str, table_cell_right_style),
        ])
    
    # Subtotal row
    data.append([
        "",
        "",
        "",
        Paragraph("<b>Ara Toplam:</b>", table_cell_right_style),
        Paragraph(f"<b>{ara_toplam:.2f} ₺</b>", table_cell_right_style),
    ])
    
    # Discount row (if applicable)
    if order.discount_percentage > 0:
        discount_amount = order.discount_amount or Decimal("0.00")
        data.append([
            "",
            "",
            "",
            Paragraph(f"<b>İndirim (%{order.discount_percentage}):</b>", table_cell_right_style),
            Paragraph(f"<b style='color:#27ae60'>-{discount_amount:.2f} ₺</b>", table_cell_right_style),
        ])
    
    # Final total row
    genel_toplam = order.final_total or ara_toplam
    data.append([
        "",
        "",
        "",
        Paragraph("<b>Genel Toplam:</b>", table_cell_right_style),
        Paragraph(f"<b>{genel_toplam:.2f} ₺</b>", table_cell_right_style),
    ])
    
    # Discount row (if applicable)
    if order.discount_percentage > 0:
        discount_amount = order.discount_amount or Decimal("0.00")
        data.append([
            "",
            "",
            "",
            Paragraph(f"<b>İndirim (%{order.discount_percentage}):</b>", table_cell_right_style),
            Paragraph(f"<b style='color:#27ae60'>-{discount_amount:.2f} ₺</b>", table_cell_right_style),
        ])
    
    # Final total row
    genel_toplam = order.final_total or ara_toplam
    data.append([
        "",
        "",
        "",
        Paragraph("<b>Genel Toplam:</b>", table_cell_right_style),
        Paragraph(f"<b>{genel_toplam:.2f} ₺</b>", table_cell_right_style),
    ])

    table = Table(
        data,
        colWidths=[25, 230, 50, 90, 90],
        hAlign="LEFT",
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), base_font),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.whitesmoke, colors.lightgrey]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0e8ff")),
        ("LINEABOVE", (0, -1), (-1, -1), 0.7, colors.black),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    footer_text = (
        "Bu fiş otomatik olarak oluşturulmuştur ve imza olmadan da geçerlidir.<br/>"
        "Master Best'i tercih ettiğiniz için teşekkür ederiz."
    )
    elements.append(Paragraph(footer_text, footer_style))

    doc.build(elements)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
