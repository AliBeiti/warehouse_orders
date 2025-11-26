from io import BytesIO
from math import ceil

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
)

from .models import Product, Order
from django.conf import settings

# ============================
#  LAYOUT DEFINITIONS BY CODE
# ============================

# ---------- PAGE 1 ----------
# First table: 214 codes (001–214) in a 20 x 11 grid
# IMPORTANT:
# If you have special codes like 008D, 009G, etc., change them manually in this list
# at the correct position (instead of "008", "009", ...).
PAGE1_TABLE1_CODES = [f"{i:03d}" for i in range(1, 215)]  # "001", "002", ..., "214"


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
    def __init__(self, codes, num_cols):
        self.codes = codes
        self.num_cols = num_cols


# PAGES: list of pages, each page = list of TableLayout
PAGES = [
    # PAGE 1
    [
        TableLayout(PAGE1_TABLE1_CODES, num_cols=20),   # 20 x 11 grid (214 codes)
    ],
    # PAGE 2
    [
        TableLayout(PAGE2_TABLE1_CODES, num_cols=20),   # CE01–CE49 (max 20 x 3)
        TableLayout(PAGE2_TABLE2_CODES, num_cols=len(PAGE2_TABLE2_CODES)),  # C01–C14 in 1 row
        TableLayout(PAGE2_TABLE3_CODES, num_cols=20),   # D01–D30 (max 2 rows, 20 cols)
    ],
    # PAGE 3 – all one row
    [
        TableLayout(PAGE3_TABLE1_CODES, num_cols=len(PAGE3_TABLE1_CODES)),  # P01–P05
        TableLayout(PAGE3_TABLE2_CODES, num_cols=len(PAGE3_TABLE2_CODES)),  # L01–L07
        TableLayout(PAGE3_TABLE3_CODES, num_cols=len(PAGE3_TABLE3_CODES)),  # R01–R06 + R01(30)
        TableLayout(PAGE3_TABLE4_CODES, num_cols=len(PAGE3_TABLE4_CODES)),  # S01–S12
        TableLayout(PAGE3_TABLE5_CODES, num_cols=len(PAGE3_TABLE5_CODES)),  # B01–B14
        TableLayout(PAGE3_TABLE6_CODES, num_cols=len(PAGE3_TABLE6_CODES)),  # PO01–PO05
        TableLayout(PAGE3_TABLE7_CODES, num_cols=len(PAGE3_TABLE7_CODES)),  # NB01–NB06
    ],
]


# ============================
#  PDF BUILDER
# ============================

def build_full_picking_pdf(order: Order) -> bytes:
    """
    Build a multi-page PDF according to the fixed code layout.
    Each code has TWO stacked cells:
        - Top cell: code (e.g. 001, CE25)
        - Bottom cell: quantity (blank if none)
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

    # Style for the layout code (top cell)
    code_style = ParagraphStyle(
        "CodeCell",
        parent=styles["Normal"],
        fontSize=9,
        leading=10,
        alignment=1,   # center
        spaceBefore=0,
        spaceAfter=0,
    )

    # Style for the quantity (bottom cell)
    qty_style = ParagraphStyle(
        "QtyCell",
        parent=styles["Normal"],
        fontSize=8,
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

    # 2) Map layout code -> Product using suffix of Product.code
    #    DB: "MBKO001" / "MBKOCE25" / "MBKOP03"
    #    Layout: "001" / "CE25" / "P03"
    products_by_code = {}
    for p in Product.objects.filter(is_active=True):
        if not p.code:
            continue

        raw = p.code.strip()
        if len(raw) <= 4:
            # Not in "XXXX<layout_code>" format, skip
            continue

        suffix = raw[4:]  # take from 5th char to end
        products_by_code[suffix] = p

    elements = []

    for page_idx, page_tables in enumerate(PAGES):
        num_tables_on_page = len(page_tables)

        for table_layout in page_tables:
            codes = table_layout.codes
            num_cols = table_layout.num_cols
            num_cells = len(codes)
            num_rows = ceil(num_cells / num_cols)  # logical rows (codes)

            # Build flat lists: one for codes, one for quantities
            codes_flat = []
            qtys_flat = []

            for code in codes:
                product = products_by_code.get(code)
                if product:
                    qty = qty_by_product_id.get(product.id, 0)
                else:
                    qty = 0

                qty_text = "" if qty == 0 else str(qty)

                codes_flat.append(Paragraph(code, code_style))
                qtys_flat.append(Paragraph(qty_text, qty_style))

            # If there are more slots than codes, pad with empty cells
            total_slots = num_rows * num_cols
            while len(codes_flat) < total_slots:
                codes_flat.append(Paragraph("", code_style))
                qtys_flat.append(Paragraph("", qty_style))

            # Build table data: for each logical row:
            #   [code cells] row
            #   [qty cells]  row
            data = []
            idx = 0
            for _ in range(num_rows):
                code_row = []
                qty_row = []
                for _ in range(num_cols):
                    code_row.append(codes_flat[idx])
                    qty_row.append(qtys_flat[idx])
                    idx += 1
                data.append(code_row)
                data.append(qty_row)

            physical_rows = len(data)  # = 2 * num_rows

            # Size calculation so tables share the page nicely
            inner_width = page_width - 2 * margin
            inner_height = page_height - 2 * margin

            # Each table gets roughly 1/N of page height
            table_height_share = inner_height / max(1, num_tables_on_page)

            row_height = table_height_share / physical_rows
            col_width = inner_width / num_cols

            table = Table(
                data,
                colWidths=[col_width] * num_cols,
                rowHeights=[row_height] * physical_rows,
            )

            table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                # Make top (code) row of each pair a bit bolder
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ]))

            elements.append(table)
            elements.append(Spacer(1, 8))

        # Page break between pages
        if page_idx != len(PAGES) - 1:
            elements.append(PageBreak())

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


def send_order_picking_pdf_to_telegram(order: Order):
    """
    Build the picking PDF for this order and send it as a document to Telegram.
    """
    pdf_bytes = build_full_picking_pdf(order)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    files = {
        "document": (
            f"order_{order.id}_picking.pdf",
            pdf_bytes,
            "application/pdf",
        )
    }

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": f"Picking PDF for Order #{order.id}",
    }

    response = requests.post(url, data=data, files=files)
    response.raise_for_status()
