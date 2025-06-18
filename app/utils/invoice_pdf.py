"""
invoice_pdf.py
إنشاء ملفات PDF عربية منسّقة (ترويسة + جدول + QR ديناميكي + تذييل)
"""

import os, qrcode, arabic_reshaper
from bidi.algorithm         import get_display
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen        import canvas
from reportlab.pdfbase       import pdfmetrics, ttfonts
from reportlab.platypus      import Table, TableStyle
from reportlab.lib           import colors
from flask                   import current_app

# ─────────── إعداد الخط العربي ───────────
AR_FONT_NAME = "Amiri"
AR_FONT_FILE = "Amiri-Regular.ttf"

def _register_arabic_font():
    """سجِّل الخط العربي إذا لم يُسجّل بعد."""
    if AR_FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return
    font_path = os.path.join(
        current_app.root_path, "static", "fonts", AR_FONT_FILE
    )
    pdfmetrics.registerFont(ttfonts.TTFont(AR_FONT_NAME, font_path))

def ar(txt: str) -> str:
    """تهيئة النص العربي ليظهر صحيحاً في ReportLab."""
    return get_display(arabic_reshaper.reshape(str(txt)))

# ─────────── عناصر جمالية مساعدة ───────────
MARGIN = 70   # ≈ 25 mm

def _draw_header(c, w, h):
    """ترويسة ملوّنة + شعار."""
    c.setFillColor("#ffffff")
    c.rect(0, h-60, w, 60, fill=1, stroke=0)

    logo = os.path.join(current_app.root_path, 'static', 'images', 'logo.png')
    c.drawImage(logo, w-120, h-55, width=90, height=40, mask='auto')

    c.setFont(AR_FONT_NAME, 18); c.setFillColor(colors.white)
    c.drawString(MARGIN, h-45, ar("منصّة جُملة – سند توريد"))

def _draw_footer(c, w):
    """تذييل ثابت فيه بيانات التواصل."""
    c.setStrokeColor('#2575fc'); c.setLineWidth(0.5)
    c.line(MARGIN, 60, w-MARGIN, 60)
    c.setFont(AR_FONT_NAME, 9); c.setFillColor(colors.black)
    msg = ar("للاستفسار: support@jumla.sa  •  9200-000-00  •  jumla.sa")
    c.drawRightString(w-MARGIN, 45, msg)

def _draw_table(c, data, start_y):
    """يرسم جدولاً مرتباً من بيانات [عنوان، قيمة]."""
    tbl = Table(data, colWidths=[120, 230])
    tbl.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (-1,-1), AR_FONT_NAME),
        ('FONTSIZE',  (0,0), (-1,-1), 11),
        ('ALIGN',     (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN',    (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('BOX',       (0,0), (-1,-1), 0.25, colors.grey),
    ]))
    tbl.wrapOn(c, 0, 0); tbl.drawOn(c, MARGIN, start_y)

# ─────────── الدالة الرئيسة ───────────
def create_invoice_pdf(voucher, order=None):
    """
    إذا order=None → PDF تفعيل أولي (status=new → active)
    إذا order موجود  → PDF فاتورة نهائية بعد الطلب (status=used)
    """
    _register_arabic_font()

    pdf_dir = current_app.config['PDF_FOLDER']
    os.makedirs(pdf_dir, exist_ok=True)

    kind      = "invoice" if order else "activation"
    filename  = f"{kind}_{voucher.code}.pdf"
    full_path = os.path.join(pdf_dir, filename)

    c = canvas.Canvas(full_path, pagesize=A4)
    w, h = A4

    # ترويسة
    _draw_header(c, w, h)

    # جدول البيانات
    y = h - 140
    rows = [
        [ar("رقم السند"), voucher.code],
        [ar("المنتج"),    voucher.product],
        [ar("الكمية"),    voucher.quantity],
        [ar("الإجمالي"),  f"{voucher.total_price:.2f} ر.س"],
    ]
    if order:
        rows += [
            [ar("اسم العميل"),  order.customer_name],
            [ar("جوال العميل"), order.customer_phone],
        ]
    _draw_table(c, rows, y)

    # ───── QR ديناميكي ─────
    base_url = current_app.config.get("BASE_URL", "").rstrip("/")
    if order is None:
        qr_url = f"{base_url}/voucher/activate/{voucher.code}"
    else:
        qr_url = f"{base_url}/voucher/order/{voucher.code}"

    qr_img  = qrcode.make(qr_url)
    qr_path = full_path.replace(".pdf", ".png")
    qr_img.save(qr_path)

    qr_x, qr_y = MARGIN, 120
    c.drawImage(qr_path, qr_x, qr_y, width=90, height=90)
    c.linkURL(qr_url, (qr_x, qr_y, qr_x+90, qr_y+90), relative=0)
    c.setFont(AR_FONT_NAME, 9)
    c.drawString(qr_x, qr_y-12, ar("امسح أو انقر لتتبع السند"))

    # تذييل
    _draw_footer(c, w)

    c.showPage(); c.save()
    # مسار نسبي ليُخزّن في قاعدة البيانات
    return f"pdfs/{filename}"
