from config import db
db.registrations.update_many({'name': 'Arjun Sharma'}, {'$set': {'attendance': False}})
db.registrations.delete_many({'name': 'Sneha Reddy'})
db.users.delete_many({'email': 'sneha@student.edu'})
print('Cleanup successful: Arjun set to Registered, Ganesh and Sneha removed.')
