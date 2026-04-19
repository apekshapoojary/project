from pymongo import MongoClient
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret123'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/'
    DB_NAME = 'event_db'

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
