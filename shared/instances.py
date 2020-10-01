import firebase_admin
import os

from firebase_admin import credentials
from flask_mongoengine import MongoEngine
from pathlib import Path

mdb = MongoEngine()

credential_path = os.path.join(
    Path(os.path.dirname(
        os.path.abspath(__file__))).parent, 'requirements.txt')


def init_firebase(config):
    cred = credentials.Certificate(
        config.FIREBASE_CREDENTIAL)
    return firebase_admin.initialize_app(
        cred, config.FIREBASE_APP)
