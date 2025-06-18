# app/routes/public.py
import os
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, send_from_directory, current_app
)
from flask_login import current_user, login_required
from app import db
from app.models import Voucher, Order, Earning
from app.utils.invoice_pdf import create_invoice_pdf

public_bp = Blueprint('public', __name__, template_folder='templates/public')

# ───────────────────── الصفحات العامة ──────────────────────
@public_bp.route('/')
def index():
    return render_template('public/index.html', latest_articles=[])

@public_bp.route('/about')
def about():
    return render_template('public/about.html')

@public_bp.route('/contact')
def contact():
    return render_template('public/contact.html')

# ───────────────────── سوق السندات (NEW) ───────────────────
@public_bp.route('/market')
@login_required
def market():
    vouchers = Voucher.query.filter_by(status='new').all()
    return render_template('public/market.html', vouchers=vouchers)

# ───────────────────── صفحة معلومات السند (GET) ───────────
@public_bp.route('/voucher/<code>', methods=['GET'], endpoint='voucher_details')
@login_required
def voucher_details(code):
    """عرض تفاصيل السند قبل سحبه."""
    voucher = Voucher.query.filter_by(code=code).first_or_404()

    # يُعرض فقط إذا كان ما زال NEW
    if voucher.status != 'new':
        flash('⚠️ هذا السند غير متاح حالياً.', 'warning')
        return redirect(url_for('public.market'))

    # توليد PDF التفعيل الأولي (إذا لم يوجد) لرؤية الـ QR
    if not voucher.invoice_path:
        voucher.invoice_path = create_invoice_pdf(voucher)
        db.session.commit()

    return render_template('public/voucher_details.html', voucher=voucher)

# ─────────── التفعيل الأول: ربط المروّج بالسند ────────────
@public_bp.route('/voucher/activate/<code>', methods=['GET', 'POST'], endpoint='activate_voucher')
@login_required
def activate_voucher(code):
    voucher = Voucher.query.filter_by(code=code).first_or_404()

    if voucher.status != 'new':
        flash('السند غير متاح للسحب.', 'warning')
        return redirect(url_for('public.market'))

    if current_user.role != 'promoter':
        flash('❌ السحب متاح للمروجين فقط.', 'danger')
        return redirect(url_for('public.voucher_details', code=code))

    # GET → صفحة تأكيد
    if request.method == 'GET':
        return render_template('public/activate_confirm.html', voucher=voucher)

    # POST → تنفيذ الربط
    voucher.status      = 'active'
    voucher.promoter_id = current_user.id
    db.session.commit()

    flash('✅ تم ربط السند بحسابك كمروج.', 'success')
    return redirect(url_for('promoter.dashboard'))

# ─────────── التفعيل الثاني: إنشاء الطلب النهائى للجمهور ───────────
@public_bp.route('/voucher/order/<code>', methods=['GET', 'POST'])
# @login_required   ← أزلناها
# @csrf_exempt      ← استخدمها إذا أردت تعطيل CSRF عن هذه الصفحة فقط
def confirm_order(code):
    voucher = Voucher.query.filter_by(code=code).first_or_404()

    # لا يُسمح إلا إذا كان السند مفعّلاً
    if voucher.status != 'active':
        flash('هذا السند غير مفعّل أو تم استخدامه.', 'warning')
        return redirect(url_for('public.market'))

    if request.method == 'POST':
        cust_name  = request.form.get('customer_name', '').strip()
        cust_phone = request.form.get('customer_phone', '').strip()

        if not cust_name or not cust_phone:
            flash('❌ يرجى إدخال الاسم ورقم الجوال.', 'danger')
            return redirect(url_for('public.confirm_order', code=code))

        # إنشاء الطلب للجمهور، وربطه بالمروّج المُسجَّل فى السند
        order = Order(
            voucher_id     = voucher.id,
            promoter_id    = voucher.promoter_id,      # الربط بالمروّج
            quantity       = voucher.quantity,
            customer_name  = cust_name,
            customer_phone = cust_phone,
            status         = 'new'
        )
        db.session.add(order)

        # تحديث السند إلى USED
        voucher.status = 'used'

        # تسجيل عمولة المروّج
        db.session.add(Earning(
            voucher_id      = voucher.id,
            promoter_id     = voucher.promoter_id,
            promoter_amount = voucher.factory_commission,
            factory_amount  = 0.0
        ))

        db.session.commit()

        return redirect(url_for('public.order_thanks', code=voucher.code))

    # GET: عرض النموذج للجمهور
    return render_template('public/confirm_order.html', voucher=voucher)


# ───────────────────── تحميل / معاينة PDF ───────────────────
@public_bp.route('/voucher/invoice/<code>')
@login_required
def download_invoice(code):
    voucher = Voucher.query.filter_by(code=code).first_or_404()

    if not voucher.invoice_path:
        flash('لم يتم توليد الفاتورة بعد.', 'warning')
        return redirect(url_for('public.voucher_details', code=code))

    pdf_dir  = current_app.config['PDF_FOLDER']
    filename = os.path.basename(voucher.invoice_path)
    return send_from_directory(pdf_dir, filename, as_attachment=True)





@public_bp.route('/voucher/thanks/<code>')
def order_thanks(code):
    voucher = Voucher.query.filter_by(code=code).first_or_404()
    if voucher.status != 'used':
        flash('لم يُنشأ طلب لهذا السند بعد.', 'warning')
        return redirect(url_for('public.market'))
    return render_template('public/order_thanks.html', voucher=voucher)


@public_bp.route('/terms')
def terms():
    return render_template('public/terms.html')

@public_bp.route('/privacy')
def privacy():
    return render_template('public/privacy.html')

@public_bp.route('/demo-login')
def demo_login():
    return render_template('public/demo_login.html')
