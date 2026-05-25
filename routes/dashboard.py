from flask import Blueprint, render_template, session, redirect, url_for
from config import db
from bson.objectid import ObjectId
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    role = session.get('role')
    
    if not user_id:
        return redirect(url_for('auth.login'))

    all_events = []
    admin_id = session.get('admin_id')
    all_events = []
    
    if role in ['admin', 'organizer']:
        if role == 'admin':
            total_events = db.events.count_documents({})
            total_registrations = db.registrations.count_documents({})
            unique_users = len(db.registrations.distinct("email"))
            recent_registrations = list(db.registrations.find().sort("_id", -1).limit(5))
        else:
            # Organizer: Filter by their own events
            my_events = list(db.events.find({"organizer_id": admin_id}))
            my_event_ids = [e['_id'] for e in my_events]
            total_events = len(my_events)
            total_registrations = db.registrations.count_documents({"event_id": {"$in": my_event_ids}})
            unique_users = len(db.registrations.distinct("email", {"event_id": {"$in": my_event_ids}}))
            recent_registrations = list(db.registrations.find({"event_id": {"$in": my_event_ids}}).sort("_id", -1).limit(5))
        
        total_users = unique_users # Use unique users for the 3rd stat
        all_events = list(db.events.find().sort("_id", -1)) # Still need all events for admin view if needed
    else:
        user_doc = db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            session.clear()
            return redirect(url_for('auth.login'))
        user_email = user_doc['email']
        recent_registrations = list(db.registrations.find({"email": user_email}).sort("_id", -1))
        
        # Filter events for students: only show upcoming/ongoing events
        today_str = datetime.now().strftime('%Y-%m-%d')
        all_events = list(db.events.find({"date": {"$gte": today_str}}).sort("date", 1))
        
        total_events = len(all_events)
        total_registrations = len(recent_registrations)
        total_users = 1 # Not used for students but keeping variable consistent
    
    for reg in recent_registrations:
        event = db.events.find_one({"_id": reg['event_id']})
        reg['event_title'] = event['title'] if event else "Unknown"
        reg['event_date'] = event['date'] if event else "N/A"
        reg['event_time'] = event.get('time', '') if event else ""
        reg['event_venue'] = event.get('venue', 'N/A') if event else "N/A"
        reg['id_str'] = str(reg['_id'])
        
    return render_template('dashboard.html', 
                           total_events=total_events, 
                           total_registrations=total_registrations,
                           total_users=total_users,
                           recent_registrations=recent_registrations,
                           all_events=all_events,
                           role=role)

@dashboard_bp.route('/scanner')
def student_scanner():
    user_id = session.get('user_id')
    role = session.get('role')
    if not user_id or role != 'student':
        return redirect(url_for('auth.login'))
    return render_template('student_scanner.html')

@dashboard_bp.route('/participants')
def participants():
    role = session.get('role')
    if role not in ['admin', 'organizer']:
        return redirect('/')
        
    registrations = list(db.registrations.find())
    for reg in registrations:
        event = db.events.find_one({"_id": reg['event_id']})
        reg['event_title'] = event['title'] if event else "Unknown"
        
    return render_template('participants.html', registrations=registrations)
