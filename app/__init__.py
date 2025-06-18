# app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

# ─── اختياري: Flask-Migrate ───────────────────────────────────────────────
try:
    from flask_migrate import Migrate
    MIGRATE_AVAILABLE = True
except ImportError:
    MIGRATE_AVAILABLE = False

# ─── تهيئة الإضافات العامة ────────────────────────────────────────────────
db            = SQLAlchemy()
login_manager = LoginManager()
csrf          = CSRFProtect()
migrate_ext   = None     # سيُهيَّأ لاحقًا إذا توفّر Flask-Migrate

# ─── factory function ─────────────────────────────────────────────────────
def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # 1) الإعدادات الأساسيّة
    app.config.from_object('app.config.Config')       # config الرئيسي
    app.config.setdefault('SECRET_KEY', 'dev-secret-key')

    # 1-B) إعدادات ملف instance/config.py (للإنتاج مثلاً)
    try:
        app.config.from_pyfile('config.py')
    except FileNotFoundError:
        pass

    # ⬇︎ تأكّد من مفاتيح مجلّدات PDF / QR و BASE_URL
    app.config.setdefault('BASE_URL',    'http://127.0.0.1:5000')
    app.config.setdefault('PDF_FOLDER',  os.path.join('app', 'static', 'pdfs'))
    app.config.setdefault('QR_FOLDER',   os.path.join('app', 'static', 'qr'))

    # 2) تهيئة الإضافات
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf.init_app(app)

    # 2-B) Flask-Migrate إذا كان متاحًا
    if MIGRATE_AVAILABLE:
        global migrate_ext
        migrate_ext = Migrate()
        migrate_ext.init_app(app, db)

    # 3) تحميل المستخدم
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 4) إتاحة csrf_token داخل جميع القوالب
    @app.context_processor
    def inject_csrf():
        return dict(csrf_token=generate_csrf)

    # 5) تسجيل الـ Blueprints
  
    from app.routes.public    import public_bp
 



   
    app.register_blueprint(public_bp)                  # الصفحات العامة

    # 6) إنشاء الجداول افتراضياً عند التشغيل الأول
    with app.app_context():
        db.create_all()
        # تأكّد أيضاً من إنشاء المجلّدات إذا لم تكن موجودة
        os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)
        os.makedirs(app.config['QR_FOLDER'],  exist_ok=True)

    return app

