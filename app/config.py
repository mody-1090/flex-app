import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(os.getcwd(), 'instance', 'app.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    QR_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'qr')
    PDF_FOLDER = os.path.join('app','static', 'pdfs')
