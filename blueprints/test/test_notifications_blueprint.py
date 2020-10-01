import firebase_admin
import json
import unittest

from mongoengine import connect, disconnect
from main import app
from blueprints.test.mock_data import *
from config import UnitTestConfig
from model.models import User, Alert, AlertRecord
from shared.instances import init_firebase


class AlertsBlueprintTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls) -> None:
        cls.firebase_app = init_firebase(UnitTestConfig)
    
    def setUp(self) -> None:
        connect("mongoenginetest", host="mongomock://localhost")
        app.config.from_object(UnitTestConfig)
        app.app_context().push()
        self.app = app.test_client()
    
    @classmethod
    def tearDownClass(cls) -> None:
        firebase_admin.delete_app(cls.firebase_app)
    
    def tearDown(self):
        disconnect()
    
