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
#  PRODUCT CODE DEFINITIONS
# ============================

# ---------- PAGE 1 ----------
# First table: 214 codes (001–214) in a 20 x 11 grid
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
# Cat Eyes: CE01 – CE49
PAGE2_TABLE1_CODES = [f"CE{i:02d}" for i in range(1, 50)]

# Candy Colors: C01 – C14
PAGE2_TABLE2_CODES = [f"C{i:02d}" for i in range(1, 15)]

# Disco Colors: D01 – D30
PAGE2_TABLE3_CODES = [f"D{i:02d}" for i in range(1, 31)]

# ---------- PAGE 3 ----------
# Painting Gel: P01 – P06
PAGE3_TABLE1_CODES = [f"P{i:02d}" for i in range(1, 7)]

# Liner Gel: L01 – L07
PAGE3_TABLE2_CODES = [f"L{i:02d}" for i in range(1, 8)]

# Rubber Base: R01 – R06 and R01(30)
PAGE3_TABLE3_CODES = [f"R{i:02d}" for i in range(1, 7)] + ["R01(30)"]

# Structure Base: S01 – S12
PAGE3_TABLE4_CODES = [f"S{i:02d}" for i in range(1, 13)]

# Builder Gel: B01 – B14
PAGE3_TABLE5_CODES = [f"B{i:02d}" for i in range(1, 15)]

# Poly Gel: PO01 – PO05
PAGE3_TABLE6_CODES = [f"PO{i:02d}" for i in range(1, 6)]

# Non-Stick Builder Gel: NB01 – NB06
PAGE3_TABLE7_CODES = [f"NB{i:02d}" for i in range(1, 7)]

# New Cateyes Kalici Oje NC01 - NC15
PAGE3_TABLE8_CODES = [f"NC{i:02d}" for i in range(1, 16)]

# Cateyes Liner Jel CL01 - CL12
PAGE3_TABLE9_CODES = [f"CL{i:02d}" for i in range(1, 13)]

# Primer
PAGE3_TABLE10_CODES = ["PR15"]

# Base Coat BC15 BC30 
PAGE3_TABLE11_CODES = ["BC15", "BC30"]

# Top Coat TC15 TC30 CTC15
PAGE3_TABLE12_CODES = ["TC15", "TC30", "CTC15"]

# Builder Liquid BL01 - BL07
PAGE3_TABLE13_CODES = [f"BL{i:02d}" for i in range(1, 8)]

# ============================
#  LAYOUT CLASSES
# ============================

class TableLayout:
    """Represents a single table with product codes."""
    def __init__(self, codes, num_cols, label=None):
        self.codes = codes          # List of product codes
        self.num_cols = num_cols    # Number of columns for this table
        self.label = label          # Category name (e.g., "GEL POLISH")


class TableRow:
    """
    Represents one horizontal row containing one or more tables side-by-side.
    
    Examples:
        # Single table taking full width:
        TableRow([TableLayout(...)])
        
        # Two tables side-by-side:
        TableRow([TableLayout(...), TableLayout(...)])
    """
    def __init__(self, tables):
        self.tables = tables  # List of TableLayout objects


# ============================
#  PAGE LAYOUT CONFIGURATION
# ============================
#
# HOW TO CONFIGURE:
# -----------------
# Each page is a list of TableRow objects.
# Each TableRow contains one or more TableLayout objects.
#
# RULES:
# 1. Put ONE table in a row if you want it to take full page width
# 2. Put MULTIPLE tables in a row to place them side-by-side
# 3. The system automatically calculates column widths proportionally
#
# EXAMPLE:
#   TableRow([table1, table2])  -> Two tables side-by-side
#   - If table1 has 10 cols and table2 has 5 cols:
#   - table1 gets 2/3 of width (10/15)
#   - table2 gets 1/3 of width (5/15)
#
# ============================

PAGES = [
    # ========== PAGE 1 ==========
    # Single large table for Gel Polish (takes full width)
    [
        TableRow([
            TableLayout(PAGE1_TABLE1_CODES, num_cols=20, label="GEL POLISH"),
        ]),
    ],
    
    # ========== PAGE 2 ==========
    # Three separate tables, each taking full width
    [
        TableRow([
            TableLayout(PAGE2_TABLE1_CODES, num_cols=20, label="CAT EYES"),
        ]),
        TableRow([
            TableLayout(PAGE2_TABLE2_CODES, num_cols=14, label="CANDY COLORS"),
        ]),
        TableRow([
            TableLayout(PAGE2_TABLE3_CODES, num_cols=20, label="DISCO COLORS"),
        ]),
        # Row 1: Painting Gel + Liner Gel + Rubber Base side-by-side
        TableRow([
            TableLayout(PAGE3_TABLE1_CODES, num_cols=6, label="PAINTING GEL"),
            TableLayout(PAGE3_TABLE2_CODES, num_cols=7, label="LINER GEL"),
            TableLayout(PAGE3_TABLE3_CODES, num_cols=7, label="RUBBER BASE"),
        ]),
    ],
    
    # ========== PAGE 3 ==========
    # Optimized layout with side-by-side tables
    [
        # Row 1: Structure Base + Poly Gel side-by-side
        TableRow([
            TableLayout(PAGE3_TABLE4_CODES, num_cols=12, label="STRUCTURE BASE"),
            TableLayout(PAGE3_TABLE6_CODES, num_cols=5, label="POLY GEL"),
        ]),
        
        # Row 2: Builder Gel + Non-Stick Builder Gel side-by-side
        TableRow([
            TableLayout(PAGE3_TABLE5_CODES, num_cols=14, label="BUILDER GEL"),
            TableLayout(PAGE3_TABLE7_CODES, num_cols=6, label="NON STICK BUILDER GEL"),
        ]),

        # Row 3: New Cateyes
        TableRow([
            TableLayout(PAGE3_TABLE8_CODES, num_cols=15, label="NEW CATEYES"),
        ]),

        # Row 4: Cateyes Liner Gel
        TableRow([
            TableLayout(PAGE3_TABLE9_CODES, num_cols=12, label="CATEYES LINER GEL"),
        ]),

        # Row 5: Primer + Base Coat + Top Coat + Builder Liquid
        TableRow([
            TableLayout(PAGE3_TABLE10_CODES, num_cols=1, label="PRIMER"),
            TableLayout(PAGE3_TABLE11_CODES, num_cols=2, label="BASE COAT"),
            TableLayout(PAGE3_TABLE12_CODES, num_cols=3, label="TOP COAT"),
            TableLayout(PAGE3_TABLE13_CODES, num_cols=7, label="BUILDER LIQUID"),
        ]),

    ],
]


# ============================
#  PDF BUILDER
# ============================

def build_full_picking_pdf(order: Order) -> bytes:
    """
    Build a multi-page picking PDF with support for side-by-side tables.
    
    Layout:
    • Page 1: Header + customer info + large Gel Polish grid
    • Pages 2-3: Category tables (single or side-by-side)
    
    Each product cell has TWO rows:
      - Top row: Product code (001, CE25, etc.)
      - Bottom row: Quantity ordered (blank if none)
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

    # Header styles
    header_title_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Title"],
        fontName="DejaVu",
        fontSize=18,
        leading=20,
        alignment=1,  # center
        textColor=colors.HexColor("#4B2E83"),
    )

    header_subtitle_style = ParagraphStyle(
        "HeaderSubtitle",
        parent=styles["Normal"],
        fontName="DejaVu",
        fontSize=11,
        leading=13,
        alignment=1,
        textColor=colors.HexColor("#4B2E83"),
    )

    header_info_value_style = ParagraphStyle(
        "HeaderInfoValue",
        parent=styles["Normal"],
        fontName="DejaVu",
        fontSize=9,
        leading=11,
        alignment=0,
    )

    # Category title style
    table_title_style = ParagraphStyle(
        "TableTitle",
        parent=styles["Heading3"],
        fontName="DejaVu",
        fontSize=12,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#4B2E83"),
        spaceAfter=4,
        spaceBefore=8,
    )

    # Note styles
    note_title_style = ParagraphStyle(
        "NoteTitle",
        parent=styles["Heading2"],
        fontName="DejaVu",
        fontSize=16,
        leading=18,
        alignment=0,
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
        alignment=0,
    )

    # Cell styles
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

    # Map order data
    qty_by_product_id = {
        item.product_id: item.quantity for item in order.items.all()
    }

    # Map layout codes to products
    products_by_code = {}
    for p in Product.objects.filter(is_active=True):
        if not p.code:
            continue
        raw = p.code.strip()
        if len(raw) <= 4:
            continue
        suffix = raw[4:]  # Extract suffix after "MBKO"
        products_by_code[suffix] = p

    elements = []

    # ========== BUILD PAGES ==========
    for page_idx, page_rows in enumerate(PAGES):
        # ---------- PAGE 1 HEADER ----------
        if page_idx == 0:
            elements.append(Paragraph("SİPARİŞ LİSTESİ", header_title_style))
            elements.append(Paragraph("MASTER BEST SİPARİŞ LİSTESİ – GEL POLISH", header_subtitle_style))
            elements.append(Spacer(1, 8))

            # Customer info
            lines = []
            if order.customer_name:
                lines.append(f"<b>İsim Soyisim:</b> {order.customer_name}")
            if order.customer_phone:
                lines.append(f"<b>Telefon:</b> {order.customer_phone}")
            if order.customer_email:
                lines.append(f"<b>E-posta:</b> {order.customer_email}")
            
            # Customer type
            if hasattr(order, 'customer_type') and order.customer_type:
                type_display = "Toptan" if order.customer_type == "wholesale" else "Perakende"
                lines.append(f"<b>Müşteri Tipi:</b> {type_display}")
            
            lines.append(f"<b>Tarih:</b> {order.created_at.strftime('%d.%m.%Y')}")

            info_html = "<br/>".join(lines)
            elements.append(Paragraph(info_html, header_info_value_style))
            elements.append(Spacer(1, 10))

        # ---------- CALCULATE AVAILABLE SPACE ----------
        inner_width = page_width - 2 * margin

        # Reserve space for headers
        if page_idx == 0:
            header_reserved = 120
            compression = 0.85
        elif page_idx == 1:
            header_reserved = 40
            compression = 0.75
        else:
            header_reserved = 40
            compression = 0.65

        available_height = page_height - 2 * margin - header_reserved
        if available_height < 80:
            available_height = page_height - 2 * margin - 60

        base_inner_height = available_height * compression

        # ---------- COUNT TOTAL ROWS FOR THIS PAGE ----------
        total_physical_rows_on_page = 0

        for table_row in page_rows:
            # Find the table in this row with the most logical rows
            max_logical_rows_in_row = 0
            for table_layout in table_row.tables:
                num_cells = len(table_layout.codes)
                logical_rows = ceil(num_cells / table_layout.num_cols)
                max_logical_rows_in_row = max(max_logical_rows_in_row, logical_rows)
            
            # Each logical row = 2 physical rows (code + qty)
            physical_rows = 2 * max_logical_rows_in_row
            total_physical_rows_on_page += physical_rows

        # Calculate uniform row height
        row_height = base_inner_height / max(1, total_physical_rows_on_page)

        # ---------- BUILD TABLE ROWS ----------
        for table_row in page_rows:
            # Calculate how many logical rows this row needs
            # (all tables in the row use the same number of logical rows)
            max_logical_rows = 0
            for table_layout in table_row.tables:
                num_cells = len(table_layout.codes)
                logical_rows = ceil(num_cells / table_layout.num_cols)
                max_logical_rows = max(max_logical_rows, logical_rows)

            physical_rows = 2 * max_logical_rows

            # Calculate total columns across all tables in this row
            total_cols = sum(t.num_cols for t in table_row.tables)
            
            # Define spacing between tables
            SPACING_PX = 30  # Total gap between tables
            num_gaps = len(table_row.tables) - 1  # Number of gaps between tables
            total_spacing = SPACING_PX * num_gaps
            
            # Available width for tables (minus spacing)
            available_table_width = inner_width - total_spacing

            # Build each table in this row
            table_elements = []
            col_widths_list = []

            for table_layout in table_row.tables:
                codes = table_layout.codes
                num_cols = table_layout.num_cols

                # Calculate this table's width (proportional to its columns, from available width)
                table_width = available_table_width * (num_cols / total_cols)
                col_width = table_width / num_cols

                # Build code and quantity lists
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

                # Pad to fill grid
                total_slots = max_logical_rows * num_cols
                while len(codes_flat) < total_slots:
                    codes_flat.append(Paragraph("", code_style))
                    qtys_flat.append(Paragraph("", qty_style))

                # Build table data (alternating code/qty rows)
                data = []
                idx = 0
                for _ in range(max_logical_rows):
                    code_row = []
                    qty_row = []
                    for _ in range(num_cols):
                        code_row.append(codes_flat[idx])
                        qty_row.append(qtys_flat[idx])
                        idx += 1
                    data.append(code_row)
                    data.append(qty_row)

                # Create table
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

                # Add label and table
                if table_layout.label:
                    table_elements.append(Paragraph(table_layout.label, table_title_style))
                
                table_elements.append(table)
                col_widths_list.append(table_width)

            # If multiple tables in this row, arrange them side-by-side
            if len(table_row.tables) > 1:
                # Create a container table with labels above each table AND spacers between
                container_data = []
                
                # Build column widths: alternating table widths and spacer widths
                final_col_widths = []
                for i, width in enumerate(col_widths_list):
                    final_col_widths.append(width)
                    # Add spacer width after each table except the last one
                    if i < len(col_widths_list) - 1:
                        final_col_widths.append(SPACING_PX)
                
                # Row 1: Labels with spacers
                label_row = []
                for i, table_layout in enumerate(table_row.tables):
                    if table_layout.label:
                        label_row.append(Paragraph(table_layout.label, table_title_style))
                    else:
                        label_row.append("")
                    # Add spacer after each label except the last one
                    if i < len(table_row.tables) - 1:
                        label_row.append("")  # Empty spacer cell
                container_data.append(label_row)
                
                # Row 2: Tables with spacers
                table_row_data = []
                for i, table_layout in enumerate(table_row.tables):
                    # Get the actual table (skip the label paragraph)
                    table_elem = table_elements[i * 2 + 1] if table_layout.label else table_elements[i]
                    table_row_data.append(table_elem)
                    # Add spacer after each table except the last one
                    if i < len(table_row.tables) - 1:
                        table_row_data.append("")  # Empty spacer cell
                container_data.append(table_row_data)

                container_table = Table(container_data, colWidths=final_col_widths)
                container_table.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                
                elements.append(container_table)
                elements.append(Spacer(1, 10))
            else:
                # Single table - add normally
                for elem in table_elements:
                    elements.append(elem)
                elements.append(Spacer(1, 10))

        # Page break between pages (except last)
        if page_idx != len(PAGES) - 1:
            elements.append(PageBreak())

    # Add customer note if present
    if order.customer_note:
        elements.append(PageBreak())
        elements.append(Paragraph("MÜŞTERİ NOTU", note_title_style))
        elements.append(Spacer(1, 12))
        note_text = order.customer_note.replace("\n", "<br/>")
        elements.append(Paragraph(note_text, note_body_style))

    doc.build(elements)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# ============================
#  TELEGRAM FUNCTIONS
# ============================

import requests

TELEGRAM_BOT_TOKEN = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = getattr(settings, "TELEGRAM_CHAT_ID", "")

def send_order_receipt_pdf_to_telegram(order: Order, pdf_content: bytes):
    """Send customer receipt PDF to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    files = {
        "document": (
            f"order_{order.id}_receipt.pdf",
            pdf_content,
            "application/pdf",
        )
    }

    # Build caption with customer type
    type_emoji = "🏪" if hasattr(order, 'customer_type') and order.customer_type == "wholesale" else "🛍️"
    type_text = "Toptan" if hasattr(order, 'customer_type') and order.customer_type == "wholesale" else "Perakende"
    
    caption = f"📄 Müşteri Fişi - Sipariş #{order.id}\n"
    caption += f"{type_emoji} Müşteri Tipi: {type_text}\n"
    caption += f"👤 {order.customer_name}\n"
    caption += f"📞 {order.customer_phone}"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": caption,
    }

    try:
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send receipt to Telegram: {e}")

def send_order_picking_pdf_to_telegram(order: Order, pdf_content):
    """Send picking PDF to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    files = {
        "document": (
            f"order_{order.id}_picking.pdf",
            pdf_content,
            "application/pdf",
        )
    }

    # Build caption with customer type
    type_emoji = "🏪" if hasattr(order, 'customer_type') and order.customer_type == "wholesale" else "🛍️"
    type_text = "Toptan" if hasattr(order, 'customer_type') and order.customer_type == "wholesale" else "Perakende"
    
    caption = f"📦 Picking List - Sipariş #{order.id}\n"
    caption += f"{type_emoji} Müşteri Tipi: {type_text}\n"
    caption += f"👤 {order.customer_name}"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": caption,
    }

    response = requests.post(url, data=data, files=files)
    response.raise_for_status()


# ============================
#  RECEIPT PDF BUILDER
# ============================

def build_order_receipt_pdf(order: Order) -> bytes:
    """
    Build a Turkish PDF receipt for the given order.
    
    Columns: #, Ürün, Adet, Birim Fiyatı, Satır Toplamı
    Includes: Master Best header, customer info, totals with discount
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
    base_font = "DejaVu" if "DejaVu" in pdfmetrics.getRegisteredFontNames() else "Helvetica"

    header_title_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Title"],
        fontName=base_font,
        fontSize=16,
        leading=18,
        alignment=1,
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
        alignment=0,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=9,
        leading=11,
        alignment=1,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=9,
        leading=11,
        alignment=0,
    )

    table_cell_right_style = ParagraphStyle(
        "TableCellRight",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=9,
        leading=11,
        alignment=2,
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

    # Header with optional logo
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

    # Customer info
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

    # Items table
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
    
    # Subtotal
    data.append([
        "",
        "",
        "",
        Paragraph("<b>Ara Toplam:</b>", table_cell_right_style),
        Paragraph(f"<b>{ara_toplam:.2f} ₺</b>", table_cell_right_style),
    ])
    
    # Discount (if applicable)
    if order.discount_percentage > 0:
        discount_amount = order.discount_amount or Decimal("0.00")
        data.append([
            "",
            "",
            "",
            Paragraph(f"<b>İndirim (%{order.discount_percentage}):</b>", table_cell_right_style),
            Paragraph(f"<b style='color:#27ae60'>-{discount_amount:.2f} ₺</b>", table_cell_right_style),
        ])
    
    # Final total
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