from flask import Flask, request, redirect
from config import Config, db
from routes.events import events_bp
from routes.registration import registration_bp
from routes.dashboard import dashboard_bp
from routes.auth import auth_bp, bcrypt
from routes.admin import admin_bp
from utils.email_service import mail
import os
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

@app.before_request
def force_https():
    # Skip static files for efficiency
    if request.path.startswith('/static'):
        return
    # Skip local development
    if request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
        return
    # Check if request was forwarded as HTTP
    if request.headers.get('X-Forwarded-Proto', 'http') == 'http':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

@app.before_request
def delete_expired_events():
    # Skip static files for efficiency
    if request.path.startswith('/static'):
        return
        
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    current_time_str = now.strftime("%H:%M")
    
    # Find all events and filter for expiration by date and time
    all_events = list(db.events.find())
    expired_event_ids = []
    
    for event in all_events:
        event_date = event.get('date')
        event_time = event.get('time')
        
        is_expired = False
        if event_date:
            if event_date < today_str:
                is_expired = True
            elif event_date == today_str:
                if event_time and event_time < current_time_str:
                    is_expired = True
                    
        if is_expired:
            expired_event_ids.append(event['_id'])
            
    if expired_event_ids:
        # Find all registrations for these events so we can delete their files
        regs = list(db.registrations.find({"event_id": {"$in": expired_event_ids}}))
        for reg in regs:
            reg_id_str = str(reg['_id'])
            paths_to_delete = [
                f"static/uploads/qr_{reg_id_str}.png",
                f"static/uploads/cert_{reg_id_str}.pdf"
            ]
            if reg.get('qr_code'):
                paths_to_delete.append(reg.get('qr_code'))
                
            for path in paths_to_delete:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
                        
        for event_id in expired_event_ids:
            event_qr_path = f"static/uploads/event_qr_{str(event_id)}.png"
            if os.path.exists(event_qr_path):
                try:
                    os.remove(event_qr_path)
                except Exception:
                    pass
                    
        # Delete registrations
        db.registrations.delete_many({"event_id": {"$in": expired_event_ids}})
        
        # Delete events
        db.events.delete_many({"_id": {"$in": expired_event_ids}})

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
