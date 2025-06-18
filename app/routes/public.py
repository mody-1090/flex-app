# app/routes/public.py
import os
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, send_from_directory, current_app
)
from flask_login import current_user, login_required
from app import db
from app.models import Voucher, Order, Earning

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


@public_bp.route('/terms')
def terms():
    return render_template('public/terms.html')

@public_bp.route('/privacy')
def privacy():
    return render_template('public/privacy.html')

@public_bp.route('/demo-login')
def demo_login():
    return render_template('public/demo_login.html')
