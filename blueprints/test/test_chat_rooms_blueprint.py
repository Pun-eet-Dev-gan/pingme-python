import firebase_admin
import json
import unittest
import pendulum
import mock

from mongoengine import connect, disconnect
from main import app
from blueprints.test.mock_data import *
from config import UnitTestConfig
from model.models import User, ChatRoom
from shared.instances import init_firebase

from firebase_admin import auth
from firebase_admin import messaging

REQUEST_TYPE_LIKE = 10
REQUEST_TYPE_FRIEND = 20


class UsersBlueprintTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls) -> None:
        cls.firebase_app = init_firebase(UnitTestConfig)
    
    def setUp(self) -> None:
        connect('mongoenginetest', host='mongomock://localhost')
        app.config.from_object(UnitTestConfig)
        app.app_context().push()
        self.app = app.test_client()
    
    @classmethod
    def tearDownClass(cls) -> None:
        firebase_admin.delete_app(cls.firebase_app)
    
    def tearDown(self):
        disconnect()
    
    def test_create_chat_room(self):
        response = self.app.post(
            "/chat_rooms", data=json.dumps(dict(title="mock_title")),
            content_type="application/json")
        
        chat_room = ChatRoom.objects.first()
        self.assertEqual(chat_room.title, "mock_title")
    
    def test_delete_chat_room(self):
        response = self.app.post(
            "/chat_rooms", data=json.dumps(dict(title="mock_title")),
            content_type="application/json")
        room_id = response.get_json()["id"]
        response = self.app.delete(
            "/chat_rooms/{room_id}".format(room_id=room_id))
        self.assertEqual(response.status_code, 200)
        chat_room = ChatRoom.objects.first()
        self.assertEqual(chat_room, None)
    
    @mock.patch.object(auth, 'verify_id_token')
    @mock.patch.object(messaging, 'send', return_value=None)
    def test_create_message(self, send, verify_id_token):
        from firebase_admin import messaging
        messaging.send = lambda x: x  # set mock function to messaging.send
        
        mock_time = pendulum.datetime(2020, 5, 21, 12)
        pendulum.set_test_now(mock_time)
        
        # insert user1
        verify_id_token.return_value = dict(uid=mock_user_1["uid"])
        self.app.post("/users", data=json.dumps(mock_user_1),
                      headers=dict(uid=mock_user_1["uid"]),
                      content_type='application/json')
        self.app.put("/users/profile", data=json.dumps(mock_user_1),
                     headers=dict(uid=mock_user_1["uid"]),
                     content_type='application/json')
        
        # insert user2
        verify_id_token.return_value = dict(uid=mock_user_2["uid"])
        self.app.post("/users", data=json.dumps(mock_user_2),
                      headers=dict(uid=mock_user_2["uid"]),
                      content_type='application/json')
        self.app.put("/users/profile", data=json.dumps(mock_user_2),
                     headers=dict(uid=mock_user_2["uid"]),
                     content_type='application/json')
        
        # open chat room with user1 and user2
        users = User.objects.all()
        user_1, user_2 = users[0], users[1]
        chat_room = ChatRoom(
            title=None,
            members=[user_1, user_2],
            members_history=[user_1, user_2],
            messages=[],
            created_at=pendulum.now().int_timestamp).save()
        
        first_message = "first_message 1"
        second_message = "second_message 2"
        
        # insert message_1
        self.app.post("/chat_rooms/{room_id}/messages/{message}".format(
            room_id=chat_room.id, message=first_message),
            headers=dict(uid=user_1.uid),
            content_type='application/json')
        
        # insert message_2
        self.app.post("/chat_rooms/{room_id}/messages/{message}".format(
            room_id=chat_room.id, message=second_message),
            headers=dict(uid=user_1.uid),
            content_type='application/json')
        
        chat_room = ChatRoom.objects.first()
        messages = chat_room.messages
        # assert messages
        self.assertEqual(len(messages), 2)
        self.assertEqual(str(messages[0].user_id), str(user_1.id))
        self.assertEqual(messages[0].message, first_message)
        self.assertEqual(str(messages[1].user_id), str(user_1.id))
        self.assertEqual(messages[1].message, second_message)
    
    @mock.patch.object(auth, 'verify_id_token')
    @mock.patch.object(messaging, 'send', return_value=None)
    def test_get_chat_room(self, send, verify_id_token):
        # insert user1
        verify_id_token.return_value = dict(uid=mock_user_1["uid"])
        self.app.post("/users", data=json.dumps(mock_user_1),
                      headers=dict(uid=mock_user_1["uid"]),
                      content_type='application/json')
        self.app.put("/users/profile", data=json.dumps(mock_user_1),
                     headers=dict(uid=mock_user_1["uid"]),
                     content_type='application/json')
        
        # insert user2
        verify_id_token.return_value = dict(uid=mock_user_2["uid"])
        self.app.post("/users", data=json.dumps(mock_user_2),
                      headers=dict(uid=mock_user_2["uid"]),
                      content_type='application/json')
        self.app.put("/users/profile", data=json.dumps(mock_user_2),
                     headers=dict(uid=mock_user_2["uid"]),
                     content_type='application/json')
        
        # open chat room with user1 and user2
        users = User.objects.all()
        user_1, user_2 = users[0], users[1]
        chat_room = ChatRoom(
            title=None,
            members=[user_1, user_2],
            members_history=[user_1, user_2],
            messages=[],
            created_at=pendulum.now().int_timestamp).save()
        
        self.app.post("/chat_rooms/{room_id}/messages/test_message_1".format(
            room_id=chat_room.id), headers=dict(uid=user_1.uid))
        
        self.app.post("/chat_rooms/{room_id}/messages/test_message_2".format(
            room_id=chat_room.id), headers=dict(uid=user_2.uid))
        
        self.app.post("/chat_rooms/{room_id}/messages/test_message_3".format(
            room_id=chat_room.id), headers=dict(uid=user_1.uid))
        
        response = self.app.get("/chat_rooms/{room_id}".format(
            room_id=chat_room.id), headers=dict(uid=user_1.uid))
        chat_room: dict = response.get_json()
        messages = chat_room.get("messages")
        members = chat_room.get("members")
        
        # checks messages
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["message"], "test_message_1")
        self.assertEqual(messages[0]["user_id"], str(user_1.id))
        self.assertEqual(messages[1]["message"], "test_message_2")
        self.assertEqual(messages[1]["user_id"], str(user_2.id))
        self.assertEqual(messages[2]["message"], "test_message_3")
        self.assertEqual(messages[2]["user_id"], str(user_1.id))
        
        # checks room members
        self.assertEqual(members[0]["uid"], user_1.uid)
        self.assertEqual(members[0]["nick_name"], user_1.nick_name)
        
        self.assertEqual(members[1]["uid"], user_2.uid)
        self.assertEqual(members[1]["nick_name"], user_2.nick_name)


if __name__ == "__main__":
    unittest.main()
