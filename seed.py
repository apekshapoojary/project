from config import db
from flask_bcrypt import Bcrypt
import os

bcrypt = Bcrypt()

def seed_data():
    print("Purging all demo data...")
    
    # Clear all collections for a clean start
    db.users.delete_many({})
    db.events.delete_many({})
    db.registrations.delete_many({})

    # Add single Administrator for initial system access
    admin_hashed = bcrypt.generate_password_hash("1234").decode('utf-8')
    db.users.insert_one({
        "name": "System Administrator",
        "email": "admin@gmail.com",
        "password": admin_hashed,
        "role": "admin"
    })
    
    print("Database purged. System Administrator account created (admin@gmail.com / 1234).")
    print("System is ready for fresh registrations.")

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    bcrypt.init_app(app)
    with app.app_context():
        seed_data()
