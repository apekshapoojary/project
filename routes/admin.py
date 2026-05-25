from flask import Blueprint, render_template, request, redirect, session, url_for, flash, jsonify, send_file
from config import db
from bson.objectid import ObjectId
import pandas as pd
import io
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
from utils.certificate_service import generate_certificate
from utils.email_service import send_certificate_email

from datetime import datetime
from utils.qr_generator import generate_qr
import os

admin_bp = Blueprint('admin', __name__)

# Admin Login Redirect (Unified in /login)
@admin_bp.route('/admin', methods=['GET'])
def admin_login():
    return redirect(url_for('auth.login'))

@admin_bp.route('/admin/dashboard')
def dashboard():
    if 'admin_id' not in session or session.get('role') not in ['admin', 'organizer']:
        return redirect(url_for('admin.admin_login'))

    role = session.get('role')
    admin_id = session.get('admin_id')

    if role == 'admin':
        total_events = db.events.count_documents({})
        total_registrations = db.registrations.count_documents({})
        total_users = db.users.count_documents({"role": "student"})
    else:
        # Organizer only sees their own stats
        my_events = list(db.events.find({"organizer_id": admin_id}))
        my_event_ids = [e['_id'] for e in my_events]
        total_events = len(my_events)
        total_registrations = db.registrations.count_documents({"event_id": {"$in": my_event_ids}})
        total_users = db.registrations.distinct("email", {"event_id": {"$in": my_event_ids}})
        total_users = len(total_users)

    return render_template(
        'admin_dashboard.html',
        total_events=total_events,
        total_registrations=total_registrations,
        total_users=total_users
    )

@admin_bp.route('/admin/events')
def admin_events():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    
    role = session.get('role')
    admin_id = session.get('admin_id')
    
    if role == 'admin':
        events = list(db.events.find())
    else:
        events = list(db.events.find({"organizer_id": admin_id}))
        
    for event in events:
        event['present_count'] = db.registrations.count_documents({"event_id": event['_id'], "attendance": True})
        event['absent_count'] = db.registrations.count_documents({"event_id": event['_id'], "attendance": False})
        
    current_date = datetime.now().strftime("%Y-%m-%d")
    return render_template('admin_events.html', events=events, current_date=current_date)

@admin_bp.route('/admin/event_qr/<event_id>')
def event_qr(event_id):
    if 'admin_id' not in session:
        return "Unauthorized", 403
        
    event = db.events.find_one({"_id": ObjectId(event_id)})
    if not event:
        return "Event not found", 404
        
    # Security: Only allow QR generation on the event day
    current_date = datetime.now().strftime("%Y-%m-%d")
    if event['date'] != current_date:
        return "QR code only available on the day of the event.", 403
        
    # Content of QR code: a link for students to click when they scan
    # Assuming students scan with their phone and are logged into the portal
    qr_content = url_for('admin.mark_attendance_self', event_id=event_id, _external=True)
    
    # Generate QR code dynamically in memory to always use the current domain (e.g. localhost or tunnel URL)
    import qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

@admin_bp.route('/mark_attendance_self/<event_id>')
def mark_attendance_self(event_id):
    if 'user_id' not in session:
        flash('Please login to mark your attendance.', 'error')
        return redirect(url_for('auth.login', next=request.full_path))
        
    user_id = session['user_id']
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    # Check if student is registered for this event
    reg = db.registrations.find_one({"email": user['email'], "event_id": ObjectId(event_id)})
    if not reg:
        flash('You are not registered for this event.', 'error')
        return redirect(url_for('events.home'))
        
    # Check if it's the event day
    event = db.events.find_one({"_id": ObjectId(event_id)})
    current_date = datetime.now().strftime("%Y-%m-%d")
    if event['date'] != current_date:
        flash('Attendance can only be marked on the day of the event.', 'error')
        return redirect(url_for('events.home'))
        
    db.registrations.update_one({"_id": reg['_id']}, {"$set": {"attendance": True}})
    flash(f'Attendance marked successfully for {event["title"]}!', 'success')
    return redirect(url_for('dashboard.dashboard'))

@admin_bp.route('/admin/participants/<event_id>')
def participants(event_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    
    role = session.get('role')
    admin_id = session.get('admin_id')
    
    if event_id == 'total':
        if role == 'admin':
            users = list(db.registrations.find())
        else:
            my_event_ids = [e['_id'] for e in db.events.find({"organizer_id": admin_id})]
            users = list(db.registrations.find({"event_id": {"$in": my_event_ids}}))
        event = None
    else:
        event = db.events.find_one({"_id": ObjectId(event_id)})
        # Security check: if organizer, verify they own this event
        if role == 'organizer' and event.get('organizer_id') != admin_id:
            flash('Unauthorized access to event participants.', 'error')
            return redirect(url_for('admin.events'))
        users = list(db.registrations.find({"event_id": ObjectId(event_id)}))
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    return render_template('admin_participants.html', 
                           users=users, 
                           event=event, 
                           current_date=current_date)

@admin_bp.route('/admin/scanner')
def scanner():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    return render_template('scanner.html')

@admin_bp.route('/admin/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'admin_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
    data = request.json
    reg_id = data.get('reg_id')
    
    if not reg_id:
        return jsonify({"status": "error", "message": "Invalid QR Data"}), 400
        
    reg = db.registrations.find_one({"_id": ObjectId(reg_id)})
    if not reg:
        return jsonify({"status": "error", "message": "Participant not found"}), 404
        
    db.registrations.update_one({"_id": ObjectId(reg_id)}, {"$set": {"attendance": True}})
    
    event = db.events.find_one({"_id": reg['event_id']})
    
    return jsonify({
        "status": "success", 
        "name": reg['name'], 
        "event": event['title'] if event else "Unknown"
    })

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

@admin_bp.route('/admin/export_participants')
@admin_bp.route('/admin/export_participants/<event_id>')
def export_participants(event_id=None):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
        
    role = session.get('role')
    admin_id = session.get('admin_id')
    
    query = {}
    if event_id and event_id != 'total':
        query['event_id'] = ObjectId(event_id)
        # Security check for organizer
        if role == 'organizer':
            event = db.events.find_one({"_id": ObjectId(event_id), "organizer_id": admin_id})
            if not event:
                flash('Unauthorized export attempt.', 'error')
                return redirect(url_for('admin.dashboard'))
    elif role == 'organizer':
        my_event_ids = [e['_id'] for e in db.events.find({"organizer_id": admin_id})]
        query['event_id'] = {"$in": my_event_ids}

    regs = list(db.registrations.find(query))
    data = []
    for r in regs:
        event = db.events.find_one({"_id": r['event_id']})
        data.append({
            "Name": r['name'],
            "Class": r.get('class_name', 'N/A'),
            "Section": r.get('section', 'N/A'),
            "Phone": r.get('phone', 'N/A'),
            "Email": r['email'],
            "Event": event['title'] if event else "N/A",
            "Status": "Present" if r.get('attendance') else "Registered"
        })
        
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Participants')
    output.seek(0)
    
    filename = f"participants_{event_id if event_id else 'all'}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@admin_bp.route('/admin/export_participants_pdf')
@admin_bp.route('/admin/export_participants_pdf/<event_id>')
def export_participants_pdf(event_id=None):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
        
    role = session.get('role')
    admin_id = session.get('admin_id')
    
    query = {}
    event_title = "All Events"
    if event_id and event_id != 'total':
        query['event_id'] = ObjectId(event_id)
        event = db.events.find_one({"_id": ObjectId(event_id)})
        if role == 'organizer' and event.get('organizer_id') != admin_id:
            flash('Unauthorized export attempt.', 'error')
            return redirect(url_for('admin.dashboard'))
        event_title = event['title']
    elif role == 'organizer':
        my_event_ids = [e['_id'] for e in db.events.find({"organizer_id": admin_id})]
        query['event_id'] = {"$in": my_event_ids}
        event_title = "My Events"

    regs = list(db.registrations.find(query))
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    elements.append(Paragraph(f"Participant List - {event_title}", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Table Data
    data = [["Name", "Class", "Email", "Event", "Status"]]
    for r in regs:
        ev = db.events.find_one({"_id": r['event_id']})
        data.append([
            r['name'],
            r.get('class_name', 'N/A'),
            r['email'],
            ev['title'] if ev else "N/A",
            "Present" if r.get('attendance') else "Registered"
        ])
    
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t)
    doc.build(elements)
    
    buffer.seek(0)
    filename = f"participants_{event_id if event_id else 'all'}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@admin_bp.route('/admin/generate_bulk_certificates')
def bulk_certificates():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
        
    regs = list(db.registrations.find({"attendance": True}))
    count = 0
    for r in regs:
        event = db.events.find_one({"_id": r['event_id']})
        if event:
            cert_path = f"static/uploads/cert_{str(r['_id'])}.pdf"
            generate_certificate(r['name'], event['title'], event['date'], cert_path)
            # Optional: send email
            # send_certificate_email(r['email'], r['name'], event['title'], cert_path)
            count += 1
            
    flash(f'Successfully generated {count} certificates for present participants.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/delete_event/<event_id>', methods=['POST'])
def delete_event(event_id):
    if 'admin_id' not in session or session.get('role') not in ['admin', 'organizer']:
        return redirect(url_for('admin.admin_login'))
        
    role = session.get('role')
    admin_id = session.get('admin_id')
    
    event = db.events.find_one({"_id": ObjectId(event_id)})
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('admin.admin_events'))
        
    # Security: Organizer can only delete their own events, Admin can delete any
    if role == 'organizer' and event.get('organizer_id') != admin_id:
        flash('Unauthorized to delete this event.', 'error')
        return redirect(url_for('admin.admin_events'))
        
    # Delete registrations first to keep database clean
    regs = list(db.registrations.find({"event_id": ObjectId(event_id)}))
    for reg in regs:
        reg_id_str = str(reg['_id'])
        paths_to_delete = [
            f"static/uploads/qr_{reg_id_str}.png",
            f"static/uploads/cert_{reg_id_str}.pdf"
        ]
        for path in paths_to_delete:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
                    
    db.registrations.delete_many({"event_id": ObjectId(event_id)})
    
    # Delete event QR code image if it exists
    event_qr_path = f"static/uploads/event_qr_{event_id}.png"
    if os.path.exists(event_qr_path):
        try:
            os.remove(event_qr_path)
        except Exception:
            pass
            
    # Delete the event itself
    db.events.delete_one({"_id": ObjectId(event_id)})
    
    flash('Event and all associated credentials have been successfully purged!', 'success')
    return redirect(url_for('admin.admin_events'))

@admin_bp.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_email', None)
    session.pop('role', None)
    return redirect(url_for('admin.admin_login'))
