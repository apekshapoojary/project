from config import db
print(f"Total events: {db.events.count_documents({})}")
print(f"Total registrations: {db.registrations.count_documents({})}")
print(f"Total users: {db.users.count_documents({})}")
print(f"Total student users: {db.users.count_documents({'role': 'student'})}")
