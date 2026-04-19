from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from config import db
from flask_bcrypt import Bcrypt

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student')

        if db.users.find_one({"email": email}):
            flash('Email already registered!', 'error')
            return redirect(url_for('auth.register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        db.users.insert_one({
            "name": name,
            "email": email,
            "password": hashed_password,
            "role": role
        })
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/login/google')
def google_login():
    from flask import current_app
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    
    # Check if we are in mock mode (placeholder ID)
    if client_id == 'PASTE_CLIENT_ID_HERE':
        # Simulate a successful Google Login for testing
        mock_user = {
            "name": "Google Test User",
            "email": "testuser@gmail.com",
            "role": "student"
        }
        user = db.users.find_one({"email": mock_user['email']})
        if not user:
            user_id = db.users.insert_one(mock_user).inserted_id
            user = db.users.find_one({"_id": user_id})
            
        session['user_id'] = str(user['_id'])
        session['role'] = user['role']
        session['name'] = user['name']
        flash('Successfully logged in via Google Simulation (Mock Mode)', 'success')
        return redirect(url_for('dashboard.dashboard'))

    redirect_uri = url_for('auth.google_callback', _external=True)
    scope = "openid email profile"
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scope}&"
        f"response_type=code"
    )
    return redirect(google_auth_url)

@auth_bp.route('/login/google/callback')
def google_callback():
    # This is where Google redirects back with a code
    # Real implementation would exchange code for tokens and log the user in
    flash('Google Authentication Handshake initiated. (Full integration requires real Client Secret)', 'info')
    return redirect(url_for('dashboard.dashboard'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('username')  # This can be name or email
        password = request.form.get('password')
        role_selected = request.form.get('role')
        
        # Check if user exists by email or name
        role_query = role_selected
        if role_selected == 'admin':
            role_query = {"$in": ["admin", "organizer"]}
            
        user = db.users.find_one({
            "$or": [{"email": identifier}, {"name": identifier}],
            "role": role_query
        })
        
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['role'] = user['role']
            session['name'] = user['name']
            
            if user['role'] in ['admin', 'organizer']:
                session['admin_id'] = str(user['_id'])
                session['admin_email'] = user['email']
                flash(f'Logged in as {user["role"].capitalize()}: {user["name"]}', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                flash(f'Welcome back, {user["name"]}!', 'success')
                return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('events.home'))
