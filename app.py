from flask import Flask
from config import Config
from routes.events import events_bp
from routes.registration import registration_bp
from routes.dashboard import dashboard_bp
from routes.auth import auth_bp, bcrypt
from routes.admin import admin_bp
from utils.email_service import mail
import os

app = Flask(__name__)
app.config.from_object(Config)

# Register Blueprints
app.register_blueprint(events_bp)
app.register_blueprint(registration_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

# Initialize Bcrypt
bcrypt.init_app(app)

# Mail Configuration (Set these to receive real emails)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') or 'YOUR_GMAIL@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD') or 'YOUR_16_DIGIT_APP_PASSWORD'
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

# Google OAuth Configuration (Get these from Google Cloud Console)
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID') or 'PASTE_CLIENT_ID_HERE'
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET') or 'PASTE_CLIENT_SECRET_HERE'

mail.init_app(app)

# Create upload folder if it doesn't exist
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if __name__ == "__main__":
    app.run(debug=True)
