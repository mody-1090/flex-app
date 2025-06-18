import os
import qrcode
from flask import current_app

def generate_qr_code(code: str) -> str:
    """
    توليد صورة QR تابعة للـ code وحفظها في QR_FOLDER.
    تُعيد المسار النسبي داخل static/qr
    """
    folder = current_app.config['QR_FOLDER']
    os.makedirs(folder, exist_ok=True)

    img = qrcode.make(code)
    filename = f"{code}.png"
    full_path = os.path.join(folder, filename)
    img.save(full_path)

    return os.path.join('qr', filename)
