import firebase_admin
import json
import os
import pendulum
import unittest
import io
import mock

from mongoengine import connect, disconnect
from main import app
from blueprints.test.mock_data import *
from blueprints import users_blueprint
from config import UnitTestConfig
from model.models import User, ChatRoom, StarRating
from shared.instances import init_firebase

from firebase_admin import auth
from firebase_admin import messaging


class UsersBlueprintTestCase(unittest.TestCase):
    
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
    
    @mock.patch.object(auth, 'verify_id_token')
    def test_create_user(self, verify_id_token):
        mock_uid = "nm7stRRXiiTVksUH39nav9I77AB2"
        verify_id_token.return_value = dict(uid=mock_uid)
        response = self.app.post(
            "/users",
            headers=dict(uid=mock_uid),
            content_type="application/json")
        user = User.objects().first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.uid, mock_uid)
    
    @mock.patch.object(auth, 'verify_id_token')
    def test_update_user(self, verify_id_token):
        verify_id_token.return_value = dict(uid=mock_user_1["uid"])
        # insert user only with uid.
        response = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        
        # update user
        response = self.app.put(
            "/users/profile",
            data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        
        updated_user = User.objects().first()
        
        self.assertEqual(updated_user["uid"], mock_user_1["uid"])
        self.assertEqual(updated_user["nick_name"], mock_user_1["nick_name"])
        self.assertEqual(updated_user["sex"], mock_user_1["sex"])
        self.assertEqual(updated_user["birthed_at"], mock_user_1["birthed_at"])
        self.assertEqual(updated_user["height"], mock_user_1["height"])
        self.assertEqual(updated_user["body_id"], mock_user_1["body_id"])
        self.assertEqual(updated_user["occupation"], mock_user_1["occupation"])
        self.assertEqual(updated_user["education"], mock_user_1["education"])
        self.assertEqual(updated_user["religion_id"], mock_user_1["religion_id"])
        self.assertEqual(updated_user["drink_id"], mock_user_1["drink_id"])
        self.assertEqual(updated_user["smoking_id"], mock_user_1["smoking_id"])
        self.assertEqual(updated_user["blood_id"], mock_user_1["blood_id"])
        self.assertEqual(updated_user["r_token"], None)
        self.assertEqual(updated_user["introduction"], mock_user_1["introduction"])
        self.assertEqual(updated_user["joined_at"], mock_user_1["joined_at"])
        self.assertEqual(updated_user["last_login_at"], mock_user_1["last_login_at"])
        self.assertEqual(len(updated_user["charm_ids"]), len(mock_user_1["charm_ids"]))
        self.assertEqual(len(updated_user["ideal_type_ids"]), len(mock_user_1["ideal_type_ids"]))
        self.assertEqual(len(updated_user["interest_ids"]), len(mock_user_1["interest_ids"]))
    
    @mock.patch.object(auth, 'verify_id_token')
    def test_override_user_list_type_values(self, verify_id_token):
        
        # insert user only with uid.
        verify_id_token.return_value = dict(uid=mock_user_1["uid"])
        response = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        
        response = self.app.put(
            "/users/profile", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        
        self.assertEqual(response.status_code, 200)
        
        # assert first update results.
        updated_user = User.objects().first()
        self.assertEqual(len(updated_user["charm_ids"]),
                         len(mock_user_1["charm_ids"]))
        self.assertEqual(len(updated_user["ideal_type_ids"]),
                         len(mock_user_1["ideal_type_ids"]))
        self.assertEqual(len(updated_user["interest_ids"]),
                         len(mock_user_1["interest_ids"]))
        
        # test for overriding list type values
        mock_user_1["charm_ids"] = mock_user_2["charm_ids"]
        mock_user_1["ideal_type_ids"] = mock_user_2["ideal_type_ids"]
        mock_user_1["interest_ids"] = mock_user_2["interest_ids"]
        
        response = self.app.put(
            "/users/profile", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        updated_user = User.objects().first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(updated_user["charm_ids"]),
                         len(mock_user_1["charm_ids"]))
        self.assertEqual(len(updated_user["ideal_type_ids"]),
                         len(mock_user_1["ideal_type_ids"]))
        self.assertEqual(len(updated_user["interest_ids"]),
                         len(mock_user_1["interest_ids"]))
    
    @mock.patch.object(auth, 'verify_id_token')
    def test_list_users(self, verify_id_token):
        # insert user1
        verify_id_token.return_value = dict(uid=mock_user_1["uid"])
        response = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        response = self.app.put(
            "/users/profile", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        # insert user2
        verify_id_token.return_value = dict(uid=mock_user_2["uid"])
        response = self.app.post(
            "/users", data=json.dumps(mock_user_2),
            headers=dict(uid=mock_user_2["uid"]),
            content_type="application/json")
        response = self.app.put(
            "/users/profile", data=json.dumps(mock_user_2),
            headers=dict(uid=mock_user_2["uid"]),
            content_type="application/json")
        
        response = self.app.get("/users")
        users = response.get_json()
        
        self.assertEqual(len(users), 2)
        user_1 = users[0]
        for key, value in mock_user_1.items():
            if key not in ["uid", "r_token", "user_images", "location"]:  # uid never shown to users.
                self.assertEqual(user_1[key], value)
        
        user_2 = users[1]
        for key, value in mock_user_2.items():
            if key not in ["uid", "r_token", "user_images", "location"]:  # uid never shown to users.
                self.assertEqual(user_2[key], value)
    
    @mock.patch.object(auth, 'verify_id_token')
    def test_get_user(self, verify_id_token):
        # insert user1
        verify_id_token.return_value = dict(uid=mock_user_1["uid"])
        response_1 = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        response_1 = self.app.put(
            "/users/profile", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        
        id_1 = response_1.get_json()["id"]
        
        # insert user2
        verify_id_token.return_value = dict(uid=mock_user_2["uid"])
        response_2 = self.app.post(
            "/users", data=json.dumps(mock_user_2),
            headers=dict(uid=mock_user_2["uid"]),
            content_type="application/json")
        response_2 = self.app.put(
            "/users/profile", data=json.dumps(mock_user_2),
            headers=dict(uid=mock_user_2["uid"]),
            content_type="application/json")
        
        id_2 = response_2.get_json()["id"]
        
        response_user_1 = self.app.get(
            "/users/{uid}".format(uid=id_1))
        response_user_2 = self.app.get(
            "/users/{uid}".format(uid=id_2))
        
        user_1 = response_user_1.get_json()
        user_2 = response_user_2.get_json()
        
        for key, value in mock_user_1.items():
            if key not in ["uid", "r_token", "user_images", "location"]:
                self.assertEqual(user_1[key], value)
        
        for key, value in mock_user_2.items():
            if key not in ["uid", "r_token", "user_images", "location"]:
                self.assertEqual(user_2[key], value)
    
    @mock.patch.object(auth, 'verify_id_token', return_value=dict(uid=mock_user_1["uid"]))
    def test_update_image(self, verify_id_token):
        """Checks for an update of an image that already exists.."""
        # mock_user_1 has images.
        uid = mock_user_1.get("uid")
        image_index_to_update = 2
        
        # insert user
        response = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        response = self.app.put(
            "/users/profile", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        
        # read file and send to server.
        file_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "testdata/nyan.png")
        
        with open(file_dir, "rb") as image:
            file = image.read()
            b = bytearray(file)
            response = self.app.post(
                "/users/user_images/{index}".format(
                    uid=uid, index=0),
                headers=dict(uid=uid),
                data=dict(file=(io.BytesIO(b), "test.jpg")),
                follow_redirects=False,
                content_type="multipart/form-data"
            )
            response = self.app.post(
                "/users/user_images/{index}".format(
                    uid=uid, index=1),
                headers=dict(uid=uid),
                data=dict(file=(io.BytesIO(b), "test.jpg")),
                follow_redirects=False,
                content_type="multipart/form-data"
            )
            response = self.app.post(
                "/users/user_images/{index}".format(
                    uid=uid, index=2),
                headers=dict(uid=uid),
                data=dict(file=(io.BytesIO(b), "test.jpg")),
                follow_redirects=False,
                content_type="multipart/form-data"
            )
        
        # retrieve it again and check
        user = User.objects(uid=uid).first()
        user_images_temp = user.user_images_temp
        
        updated_image_temp = user_images_temp[image_index_to_update]
        original_image = mock_user_1["user_images"][image_index_to_update]
        
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(original_image["url"], updated_image_temp["url"])
        self.assertEqual(user.available, False)
        self.assertEqual(user.status, 0)
    
    @mock.patch.object(auth, 'verify_id_token', return_value=dict(uid=mock_user_1["uid"]))
    def test_delete_image(self, verify_id_token):
        """Checks for deletion of an image that already exists.."""
        
        # mock_user_1 has images.
        uid = mock_user_1.get("uid")
        
        # insert user
        response = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        
        # read file and send to server.
        file_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "testdata/nyan.png")
        
        with open(file_dir, "rb") as image:
            file = image.read()
            b = bytearray(file)
            response = self.app.post(
                "/users/user_images/{index}".format(
                    uid=uid, index=0),
                headers=dict(uid=uid),
                data=dict(file=(io.BytesIO(b), "test.jpg")),
                follow_redirects=False,
                content_type="multipart/form-data"
            )
            response = self.app.post(
                "/users/user_images/{index}".format(
                    uid=uid, index=1),
                headers=dict(uid=uid),
                data=dict(file=(io.BytesIO(b), "test.jpg")),
                follow_redirects=False,
                content_type="multipart/form-data"
            )
            response = self.app.post(
                "/users/user_images/{index}".format(
                    uid=uid, index=2),
                headers=dict(uid=uid),
                data=dict(file=(io.BytesIO(b), "test.jpg")),
                follow_redirects=False,
                content_type="multipart/form-data"
            )
        
        # delete user image using index.
        response = self.app.delete(
            "/users/user_images/{index}".format(index=2),
            headers=dict(uid=uid),
            content_type="application/json")
        
        user = User.objects.first()
        self.assertEqual(len(user.user_images_temp), 2)
        self.assertEqual(user.available, False)
        self.assertEqual(user.status, 0)
    
    @mock.patch.object(auth, 'verify_id_token')
    def test_updated_image_images_pending_order(self, verify_id_token):
        """Checks for an update of an image that already exists.."""
        
        # mock_user_1 has images.
        uid = mock_user_1.get("uid")
        verify_id_token.return_value = dict(uid=uid)
        # insert user
        response = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        response = self.app.put(
            "/users/profile", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        
        # read file and send to server.
        file_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "testdata/nyan.png")
        
        with open(file_dir, "rb") as image:
            file = image.read()
            b = bytearray(file)
            response_1 = self.app.post(
                "/users/user_images/{index}".format(index=5),
                headers=dict(uid=uid),
                data=dict(file=(io.BytesIO(b), "test.jpg")),
                follow_redirects=False,
                content_type="multipart/form-data"
            )
            response_2 = self.app.post(
                "/users/user_images/{index}".format(index=4),
                headers=dict(uid=uid),
                data=dict(file=(io.BytesIO(b), "test.jpg")),
                follow_redirects=False,
                content_type="multipart/form-data"
            )
            response_3 = self.app.post(
                "/users/user_images/{index}".format(
                    uid=uid, index=3),
                headers=dict(uid=uid),
                data=dict(file=(io.BytesIO(b), "test.jpg")),
                follow_redirects=False,
                content_type="multipart/form-data"
            )
        
        # retrieve it again and check
        user = User.objects(uid=uid).first()
        
        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(response_2.status_code, 200)
        self.assertEqual(response_3.status_code, 200)
        
        self.assertEqual(len(user.user_images_temp), 3)
        self.assertEqual(user.user_images_temp[0].index, 3)
        self.assertEqual(user.user_images_temp[1].index, 4)
        self.assertEqual(user.user_images_temp[2].index, 5)
    
    @mock.patch.object(auth, 'verify_id_token')
    def test_insert_image_pending(self, verify_id_token):
        """Checks for an insert of an new image.."""
        # mock_user_2 has no images.
        uid = mock_user_2.get("uid")
        index_to_test = 2
        
        # insert user
        verify_id_token.return_value = dict(uid=uid)
        response = self.app.post(
            "/users", data=json.dumps(mock_user_2),
            headers=dict(uid=mock_user_2["uid"]),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        
        response = self.app.put(
            "/users/profile", data=json.dumps(mock_user_2),
            headers=dict(uid=mock_user_2["uid"]),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        
        # read file and send to server.
        file_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "testdata/nyan.png")
        
        with open(file_dir, "rb") as image:
            file = image.read()
            b = bytearray(file)
            response = self.app.post(
                "/users/user_images/{index}".format(
                    index=index_to_test),
                data=dict(file=(io.BytesIO(b), "test.jpg")),
                headers=dict(uid=uid),
                follow_redirects=False,
                content_type="multipart/form-data"
            )
        
        user = User.objects(uid=uid).first_or_404()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(user.user_images_temp), 1)
        self.assertEqual(user.user_images_temp[0].index, index_to_test)
        self.assertRegex(user.user_images_temp[0].url, "https://storage.googleapis.com.*")
    
    @mock.patch.object(auth, 'verify_id_token', return_value=dict(uid=mock_user_1["uid"]))
    def test_update_registration_token(self, verify_id_token):
        # insert an user
        response = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        response = self.app.put(
            "/users/profile", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        # update the user
        self.app.put("/users/r_token/{r_token}".format(
            r_token="updated_registration_token_value"),
            headers=dict(uid=mock_user_1["uid"]))
        
        user_1 = User.objects(uid=mock_user_1["uid"]).first()
        # registration_token must be updated.
        self.assertEqual(user_1.r_token, "updated_registration_token_value")
    
    @mock.patch.object(auth, 'verify_id_token')
    @mock.patch.object(messaging, 'send', return_value=None)
    def test_list_chat_rooms(self, send, verify_id_token):
        # insert user1
        verify_id_token.return_value = dict(uid=mock_user_1["uid"])
        response = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        response = self.app.put(
            "/users/profile", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        # insert user2
        verify_id_token.return_value = dict(uid=mock_user_2["uid"])
        response = self.app.post(
            "/users", data=json.dumps(mock_user_2),
            headers=dict(uid=mock_user_2["uid"]),
            content_type="application/json")
        response = self.app.put(
            "/users/profile", data=json.dumps(mock_user_2),
            headers=dict(uid=mock_user_2["uid"]),
            content_type="application/json")
        # insert user3
        verify_id_token.return_value = dict(uid=mock_user_3["uid"])
        response = self.app.post(
            "/users", data=json.dumps(mock_user_3),
            headers=dict(uid=mock_user_3["uid"]),
            content_type="application/json")
        response = self.app.put(
            "/users/profile", data=json.dumps(mock_user_3),
            headers=dict(uid=mock_user_3["uid"]),
            content_type="application/json")
        
        # open chat room with user1 and user2
        users = User.objects.all()
        user_1, user_2, user_3 = users[0], users[1], users[2]
        chat_room_1 = ChatRoom(
            title=None,
            members=[user_1, user_2],
            members_history=[user_1, user_2],
            messages=[],
            created_at=pendulum.now().int_timestamp
        ).save()
        chat_room_2 = ChatRoom(
            title=None,
            members=[user_2, user_3],
            members_history=[user_2, user_3],
            messages=[],
            created_at=pendulum.now().int_timestamp
        ).save()
        
        # insert messages only to room_1
        self.app.post("/chat_rooms/{room_id}/messages/{message}".format(
            room_id=chat_room_1.id, message="test_message_1"),
            headers=dict(uid=user_1.uid),
            content_type="application/json")
        
        self.app.post("/chat_rooms/{room_id}/messages/{message}".format(
            room_id=chat_room_1.id, message="test_message_2"),
            headers=dict(uid=user_2.uid),
            content_type="application/json")
        
        self.app.post("/chat_rooms/{room_id}/messages/{message}".format(
            room_id=chat_room_1.id, message="test_message_3"),
            headers=dict(uid=user_1.uid),
            content_type="application/json")
        
        response = self.app.get(
            "/users/{uid}/chat_rooms".format(uid=user_2.uid))
        rooms = response.get_json()
        room_1, room_2 = rooms[0], rooms[1]
        
        # members validation
        room_1_members, room_2_members = \
            room_1["members"], room_2["members"]
        self.assertEqual(room_1_members[0]["uid"], mock_user_1["uid"])
        self.assertEqual(room_1_members[1]["uid"], mock_user_2["uid"])
        self.assertEqual(room_2_members[0]["uid"], mock_user_2["uid"])
        self.assertEqual(room_2_members[1]["uid"], mock_user_3["uid"])
        
        # messages validation
        room_1_messages, room_2_messages = room_1["messages"], room_2["messages"]
        self.assertEqual(room_1_messages[0]["message"], "test_message_1")
        self.assertEqual(room_1_messages[1]["message"], "test_message_2")
        self.assertEqual(room_1_messages[2]["message"], "test_message_3")
        self.assertEqual(len(room_2_messages), 0)
    
    @mock.patch.object(auth, 'verify_id_token', return_value=dict(uid=mock_user_1["uid"]))
    def test_list_user_posts(self, verify_id_token):
        # insert user_1
        response = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        response = self.app.put(
            "/users/profile", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        
        user_just_created = User.objects.first()
        
        # when nothing post found
        response = self.app.get(
            "/users/{user_id}/posts".format(
                user_id=user_just_created["id"]))
        self.assertEqual(response.status_code, 200)
        
        # insert post1
        file_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "testdata/nyan.png")
        with open(file_dir, "rb") as image:
            b = bytearray(image.read())
            self.app.post(
                "/posts",
                data=dict(title="mock_title",
                          description="mock_description",
                          post_image=(io.BytesIO(b), "test.jpg")),
                headers=dict(uid=mock_user_1["uid"]),
                follow_redirects=False,
                content_type="multipart/form-data")
        
        # when 1 post found
        response = self.app.get(
            "/users/{user_id}/posts".format(user_id=user_just_created["id"]))
        posts = response.get_json()
        self.assertEqual(
            response.status_code, 200)
        self.assertEqual(
            posts[0]["title"], "mock_title")
        self.assertEqual(
            posts[0]["description"], "mock_description")
        self.assertRegex(
            posts[0]["url"], "https://storage.googleapis.com/.*")
    
    @mock.patch.object(auth, 'verify_id_token')
    @mock.patch.object(messaging, 'send', return_value=None)
    def test_poke(self, mock_send, verify_id_token):
        # insert user_1
        verify_id_token.return_value = dict(uid=mock_user_1["uid"])
        response_1 = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        response_1 = self.app.put(
            "/users/profile", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        
        # insert user_2
        verify_id_token.return_value = dict(uid=mock_user_2["uid"])
        response_2 = self.app.post(
            "/users", data=json.dumps(mock_user_2),
            headers=dict(uid=mock_user_2["uid"]),
            content_type="application/json")
        response_2 = self.app.put(
            "/users/profile", data=json.dumps(mock_user_2),
            headers=dict(uid=mock_user_2["uid"]),
            content_type="application/json")
        
        user_from = response_1.get_json()
        user_to = response_2.get_json()
        
        # user_1 pokes user_2
        poke_response = self.app.post(
            "/users/poke/{uid_to}".format(
                uid_to=user_to["id"]),
            headers=dict(uid=user_from["uid"]))
        self.assertEqual(poke_response.status_code, 200)
        self.assertEqual(mock_send.call_count, 1)
    
    @mock.patch.object(auth, 'verify_id_token')
    def test_user_images_approval(self, verify_id_token):
        
        uid = mock_user_1.get("uid")
        
        verify_id_token.return_value = dict(uid=uid)
        response_1 = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=uid),
            content_type="application/json")
        response_1 = self.app.put(
            "/users/profile", data=json.dumps(mock_user_1),
            headers=dict(uid=uid),
            content_type="application/json")
        
        # read file and send to server.
        file_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "testdata/nyan.png")
        
        with open(file_dir, "rb") as image:
            file = image.read()
            b = bytearray(file)
            
            response = self.app.post(
                "/users/user_images/{index}".format(
                    uid=uid, index=0),
                headers=dict(uid=uid),
                data=dict(file=(io.BytesIO(b), "test.jpg")),
                follow_redirects=False,
                content_type="multipart/form-data")
            self.assertEqual(response.status_code, 200)
            
            response = self.app.post(
                "/users/user_images/{index}".format(index=1),
                headers=dict(uid=uid),
                data=dict(file=(io.BytesIO(b), "test.jpg")),
                follow_redirects=False,
                content_type="multipart/form-data")
            self.assertEqual(response.status_code, 200)
            
            response = self.app.post(
                "/users/user_images/{index}".format(index=2),
                headers=dict(uid=uid),
                data=dict(file=(io.BytesIO(b), "test.jpg")),
                follow_redirects=False,
                content_type="multipart/form-data")
            self.assertEqual(response.status_code, 200)
        
        # retrieve it again and check
        user = User.objects(uid=uid).first()
        self.assertEqual(len(user.user_images), 0)
        self.assertEqual(len(user.user_images_temp), 3)
        
        response = self.app.put(
            "/users/{user_id}/status/approval".format(
                user_id=str(user.id)))
        
        user = User.objects(uid=uid).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(user.user_images), 3)
        self.assertEqual(len(user.user_images_temp), 3)
        
        for index, _ in enumerate(user.user_images):
            self.assertEqual(user.user_images[index], user.user_images_temp[index])
    
    @mock.patch.object(auth, 'verify_id_token')
    def test_update_location(self, mock_verify_id_token):
        # insert user_1
        mock_verify_id_token.return_value = dict(uid=mock_user_1["uid"])
        response_1 = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        
        self.assertEqual(response_1.status_code, 200)
        
        location_response = self.app.put(
            "/users/location?longitude=127.07256&latitude=35.78125",
            headers=dict(uid=mock_user_1["uid"]))
        
        self.assertEqual(location_response.status_code, 200)
        
        user = User.objects.first()
        coordinates = user.location.get("coordinates")
        self.assertEqual(coordinates, [127.07256, 35.78125])
        
        if __name__ == "__main__":
            unittest.main()
    
    @mock.patch.object(users_blueprint, 'get_coordinates_by_ip', return_value=[127.07256, 35.78125])
    @mock.patch.object(auth, 'verify_id_token')
    def test_update_location_by_ip(
            self, mock_verify_id_token, mock_get_coordinates_by_ip):
        # insert user_1
        mock_verify_id_token.return_value = dict(uid=mock_user_1["uid"])
        response_1 = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        
        self.assertEqual(response_1.status_code, 200)
        
        location_response = self.app.put(
            "/users/location",
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        
        self.assertEqual(location_response.status_code, 200)
        
        user = User.objects.first()
        coordinates = user.location.get("coordinates")
        self.assertEqual(coordinates, [127.07256, 35.78125])
    
    @mock.patch.object(auth, 'verify_id_token')
    @mock.patch.object(messaging, 'send', return_value=None)
    def test_update_star_rating_score(self, mock_send, mock_verify_id_token):
        # insert user_1
        mock_verify_id_token.return_value = dict(uid=mock_user_1["uid"])
        response = self.app.post(
            "/users", data=json.dumps(mock_user_1),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        
        self.assertEqual(response.status_code, 200)
        
        # insert user_2
        mock_verify_id_token.return_value = dict(uid=mock_user_2["uid"])
        response = self.app.post(
            "/users", data=json.dumps(mock_user_2),
            headers=dict(uid=mock_user_2["uid"]),
            content_type="application/json")
        
        self.assertEqual(response.status_code, 200)
        
        # user 1 rates score to user 2
        user_id = str(User.objects(uid=mock_user_2["uid"]).first().id)
        response = self.app.put(
            "/users/{user_id}/score/{score}".format(
                user_id=user_id, score=5),
            headers=dict(uid=mock_user_1["uid"]),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        
        rate = StarRating.objects.first()
        
        self.assertEqual(rate.user_from.uid, mock_user_1["uid"])
        self.assertEqual(rate.user_to.uid, mock_user_2["uid"])
        self.assertEqual(rate.score, 5)
    
    if __name__ == "__main__":
        unittest.main()
