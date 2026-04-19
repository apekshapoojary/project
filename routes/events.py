from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from config import db
from bson.objectid import ObjectId

events_bp = Blueprint('events', __name__)

@events_bp.route('/')
def home():
    if 'user_id' in session or 'admin_id' in session:
        role = session.get('role')
        if role in ['admin', 'organizer']:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))

@events_bp.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if 'admin_id' not in session and session.get('role') not in ['admin', 'organizer']:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        data = {
            "title": request.form['title'],
            "date": request.form['date'],
            "venue": request.form['venue'],
            "description": request.form['description'],
            "coordinator": request.form.get('coordinator', 'N/A'),
            "reg_start": request.form['reg_start'],
            "reg_deadline": request.form['reg_deadline'],
            "organizer_id": session.get('admin_id') or session.get('user_id')  # Link to creator
        }
        db.events.insert_one(data)
        flash('Event created successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('create_event.html')

@events_bp.route('/event/<event_id>')
def event_details(event_id):
    event = db.events.find_one({"_id": ObjectId(event_id)})
    return render_template('event_details.html', event=event)
