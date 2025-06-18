# app/models.py

import random
import string
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db

# ─────────────────────────────────────────────────────────────────────────────
# 1) جدول المستخدم الأساسي
# ─────────────────────────────────────────────────────────────────────────────
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id            = db.Column(db.Integer,   primary_key=True)
    username      = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role          = db.Column(db.String(20), nullable=False)  # factory | promoter | admin
    factory_id    = db.Column(db.Integer, db.ForeignKey('factories.id'))

    # علاقة واحد-إلى-واحد مع المروج (إن وجد)
    promoter = db.relationship('Promoter', back_populates='user', uselist=False)

    @property
    def password(self):
        raise AttributeError("كلمة المرور لا يمكن قراءتها مباشرةً.")

    @password.setter
    def password(self, plain):
        self.password_hash = generate_password_hash(plain)

    def check_password(self, plain):
        return check_password_hash(self.password_hash, plain)

    @property
    def is_promoter(self) -> bool:
        return self.role == 'promoter'


# ─────────────────────────────────────────────────────────────────────────────
# 2) جدول المصانع
# ─────────────────────────────────────────────────────────────────────────────
class Factory(db.Model):
    __tablename__ = 'factories'

    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(128), nullable=False)
    contact_person  = db.Column(db.String(128))
    contact_phone   = db.Column(db.String(32))
    commission_rate = db.Column(db.Float, default=1.0)  # ريال لكل كرتون

    vouchers = db.relationship('Voucher', back_populates='factory')


# ─────────────────────────────────────────────────────────────────────────────
# 3) جدول المروِّجين
# ─────────────────────────────────────────────────────────────────────────────
class Promoter(db.Model):
    __tablename__ = 'promoters'

    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String(128), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # روابط ORM
    user     = db.relationship('User',      back_populates='promoter')
    vouchers = db.relationship('Voucher',   back_populates='promoter', lazy='dynamic')
    orders   = db.relationship('Order',     back_populates='promoter', lazy='dynamic')
    earnings = db.relationship('Earning',   back_populates='promoter')


# ─────────────────────────────────────────────────────────────────────────────
# 4) جدول السندات
# ─────────────────────────────────────────────────────────────────────────────
class Voucher(db.Model):
    __tablename__ = 'vouchers'

    id                 = db.Column(db.Integer, primary_key=True)
    code               = db.Column(db.String(32), unique=True, nullable=False)
    product            = db.Column(db.String(128), nullable=False)
    quantity           = db.Column(db.Integer, nullable=False)
    status             = db.Column(db.String(20), default='new')  # new|active|used
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)
    qr_path            = db.Column(db.String(256))
    invoice_path       = db.Column(db.String(256))

    factory_id         = db.Column(db.Integer, db.ForeignKey('factories.id'))
    promoter_id        = db.Column(db.Integer, db.ForeignKey('promoters.id'))

    factory_commission = db.Column(db.Float, default=0.0)
    price_per_unit     = db.Column(db.Float, default=0.0)
    vat_rate           = db.Column(db.Float, default=0.15)
    total_price        = db.Column(db.Float, default=0.0)

    # روابط ORM
    factory  = db.relationship('Factory',  back_populates='vouchers')
    promoter = db.relationship('Promoter', back_populates='vouchers')

    # علاقة 1-إلى-1 مع الطلب النهائي
    order    = db.relationship('Order', back_populates='voucher', uselist=False)

    @staticmethod
    def generate_unique_code(length: int = 8) -> str:
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            if not Voucher.query.filter_by(code=code).first():
                return code

    @property
    def promoter_name(self) -> str:
        return self.promoter.user.username if self.promoter else None


# ─────────────────────────────────────────────────────────────────────────────
# 5) جدول الأرباح
# ─────────────────────────────────────────────────────────────────────────────
class Earning(db.Model):
    __tablename__ = 'earnings'

    id              = db.Column(db.Integer, primary_key=True)
    voucher_id      = db.Column(db.Integer, db.ForeignKey('vouchers.id'))
    promoter_id     = db.Column(db.Integer, db.ForeignKey('promoters.id'))
    factory_amount  = db.Column(db.Float, nullable=False)
    promoter_amount = db.Column(db.Float, nullable=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    # روابط ORM
    promoter = db.relationship('Promoter', back_populates='earnings')
    voucher  = db.relationship('Voucher', backref=db.backref('earnings', lazy='dynamic'))


# ─────────────────────────────────────────────────────────────────────────────
# 6) جدول طلبات السحب
# ─────────────────────────────────────────────────────────────────────────────
class Withdrawal(db.Model):
    __tablename__ = 'withdrawals'

    id           = db.Column(db.Integer, primary_key=True)
    promoter_id  = db.Column(db.Integer, db.ForeignKey('promoters.id'))
    amount       = db.Column(db.Float,  nullable=False)
    status       = db.Column(db.String(20), default='pending')  # pending|approved|rejected
    factory_note = db.Column(db.String(256))                    # سبب الرفض
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    dispute      = db.relationship('Dispute', back_populates='withdrawal', uselist=False)
    promoter     = db.relationship('Promoter', backref=db.backref('withdrawals', lazy='dynamic'))


# ─────────────────────────────────────────────────────────────────────────────
# 7) جدول الطلبات النهائية
# ─────────────────────────────────────────────────────────────────────────────
class Order(db.Model):
    __tablename__ = 'orders'

    id             = db.Column(db.Integer, primary_key=True)
    voucher_id     = db.Column(db.Integer, db.ForeignKey('vouchers.id'))
    promoter_id    = db.Column(db.Integer, db.ForeignKey('promoters.id'))
    quantity       = db.Column(db.Integer, nullable=False)
    customer_name  = db.Column(db.String(128))
    customer_phone = db.Column(db.String(32))
    status         = db.Column(db.String(20), default='new')  # new|in_progress|done
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    # روابط ORM
    voucher   = db.relationship('Voucher',  back_populates='order')
    promoter  = db.relationship('Promoter', back_populates='orders')


# ─────────────────────────────────────────────────────────────────────────────
# 8) جدول التظلم
# ─────────────────────────────────────────────────────────────────────────────
class Dispute(db.Model):
    __tablename__ = 'disputes'

    id            = db.Column(db.Integer, primary_key=True)
    withdrawal_id = db.Column(db.Integer, db.ForeignKey('withdrawals.id'))
    reason        = db.Column(db.Text, nullable=False)
    status        = db.Column(db.String(20), default='open')  # open|resolved
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    withdrawal    = db.relationship('Withdrawal', back_populates='dispute')


# ─────────────────────────────────────────────────────────────────────────────
# 9) جدول سجلات النظام
# ─────────────────────────────────────────────────────────────────────────────
class LogEntry(db.Model):
    __tablename__ = 'log_entries'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action     = db.Column(db.String(256), nullable=False)
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)

    user       = db.relationship('User', backref=db.backref('logs', lazy='dynamic'))

    def __repr__(self):
        return f"<LogEntry {self.id} by {self.user_id or 'anon'} @ {self.timestamp}>"


# ─────────────────────────────────────────────────────────────────────────────
# 10) جدول التقارير
# ─────────────────────────────────────────────────────────────────────────────
class Report(db.Model):
    __tablename__ = 'reports'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(128), nullable=False)
    payload     = db.Column(db.JSON,       nullable=False)
    created_at  = db.Column(db.DateTime,   default=datetime.utcnow)

    @staticmethod
    def generate_summary():
        from app.models import Factory, Promoter, Voucher, Order
        return {
            'factories_count': Factory.query.count(),
            'promoters_count': Promoter.query.count(),
            'vouchers_new'   : Voucher.query.filter_by(status='new').count(),
            'orders_pending' : Order.query.filter_by(status='new').count(),
        }

    def __repr__(self):
        return f"<Report {self.name} @ {self.created_at}>"
