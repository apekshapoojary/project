from config import db
from bson.objectid import ObjectId
from utils.qr_generator import generate_qr
from utils.certificate_service import generate_certificate
from utils.email_service import send_registration_email
from flask import send_file, Blueprint, request, redirect, url_for, flash, render_template
import os

registration_bp = Blueprint('registration', __name__)

@registration_bp.route('/register/<event_id>', methods=['POST'])
def register(event_id):
    name = request.form.get('name')
    email = request.form.get('email')
    
    if not name or not email:
        flash('Please provide both name and email.', 'error')
        return redirect(url_for('events.event_details', event_id=event_id))

    from datetime import datetime
    registration_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    registration_data = {
        "name": name,
        "email": email,
        "class_name": request.form.get('class_name'),
        "section": request.form.get('section'),
        "phone": request.form.get('phone'),
        "event_id": ObjectId(event_id),
        "attendance": False,
        "timestamp": registration_time
    }
    
    # Check if already registered
    existing = db.registrations.find_one({"email": email, "event_id": ObjectId(event_id)})
    if existing:
        flash('You are already registered for this event.', 'error')
    else:
        # Insert registration record
        db.registrations.insert_one(registration_data)
        
        # Send Confirmation Email
        event = db.events.find_one({"_id": ObjectId(event_id)})
        if event:
            from utils.email_service import send_registration_email
            send_registration_email(
                to_email=email,
                user_name=name,
                event_name=event['title'],
                event_date=event['date'],
                registration_time=registration_time
            )
        
        flash('Registration successful! Please check your email for confirmation.', 'success')
    
    return redirect(url_for('dashboard.dashboard'))

@registration_bp.route('/download_certificate/<reg_id>')
def download_certificate(reg_id):
    reg = db.registrations.find_one({"_id": ObjectId(reg_id)})
    if not reg:
        flash('Registration record not found.', 'error')
        return redirect(url_for('events.home'))
    
    event = db.events.find_one({"_id": reg['event_id']})
    event_name = event['title'] if event else "Event"
    event_date = event['date'] if event else "N/A"
    
    cert_path = f"static/uploads/cert_{reg_id}.pdf"
    generate_certificate(reg['name'], event_name, event_date, cert_path)
    
    return send_file(cert_path, as_attachment=True)
