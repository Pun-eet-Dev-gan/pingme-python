import firebase_admin
import json
import io
import os
import random
import unittest
import uuid
import pendulum

from main import app
from config import TestConfig
from model.models import Post, Comment, User, ChatRoom, Request, Alert
from shared.instances import init_firebase, mdb


class PostsBlueprintTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls) -> None:
        cls.firebase_app = init_firebase(TestConfig)
    
    def setUp(self) -> None:
        app.config.from_object(TestConfig)
        mdb.init_app(app)
        app.app_context().push()
        self.app = app.test_client()
    
    @classmethod
    def tearDownClass(cls) -> None:
        firebase_admin.delete_app(cls.firebase_app)
    
    def test_create_post(self):
        """Checks to create a post properly."""
        
        users = User.objects.all()
        user_1 = users[0]
        user_2 = users[1]
        
        # insert user then create post
        file_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'testdata/nyan.png')
        
        # insert post1
        for i in range(2, 20):
            with open(file_dir, "rb") as image:
                b = bytearray(image.read())
                response = self.app.post(
                    "/posts/users/{uid}".format(uid=user_2["uid"]),
                    data=dict(title="dummy_title{0}".format(i),
                              description="dummy_description",
                              post_image=(io.BytesIO(b), 'test.jpg')),
                    follow_redirects=False,
                    content_type='multipart/form-data')
    
    def test_send_message_to_chat_room(self):
        chat_rooms = ChatRoom.objects.all()
        room_id = chat_rooms[0].id
        uid = chat_rooms[0].members[0].uid
        # insert message_1
        self.app.post("/chat_rooms/{room_id}/users/{uid}".format(
            room_id=room_id, uid=uid),
            data=json.dumps(dict(message="321321321")),
            content_type='application/json')
        print(chat_rooms)
    
    def test_insert_mock_user_dump(self):
        # GxM4qD1jPMUo80TrrGHx9JI4OnO2
        # W56U9v84nfXiM842el1EWgENuzo1
        
        male_images = [
            dict(index=0,
                 url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/W56U9v84nfXiM842el1EWgENuzo1_0_9280f814-ead6-11ea-9038-907841698cfa"),
            dict(index=1,
                 url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/W56U9v84nfXiM842el1EWgENuzo1_1_999790cc-ead6-11ea-9038-907841698cfa"),
            dict(index=2,
                 url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/W56U9v84nfXiM842el1EWgENuzo1_2_a3a38abc-ead6-11ea-9038-907841698cfa"),
            dict(index=3,
                 url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/W56U9v84nfXiM842el1EWgENuzo1_3_920579c2-ead7-11ea-8b30-907841698cfa"),
            dict(index=4,
                 url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/W56U9v84nfXiM842el1EWgENuzo1_4_9ae50bf2-ead7-11ea-8b30-907841698cfa"),
            dict(index=5,
                 url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/W56U9v84nfXiM842el1EWgENuzo1_5_a475a41a-ead7-11ea-8b30-907841698cfa")
        ]
        
        female_images = [
            dict(index=0,
                 url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/GxM4qD1jPMUo80TrrGHx9JI4OnO2_0_c185da2c-ead5-11ea-9038-907841698cfa"),
            dict(index=1,
                 url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/GxM4qD1jPMUo80TrrGHx9JI4OnO2_1_e747faf6-ead5-11ea-9038-907841698cfa"),
            dict(index=2,
                 url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/GxM4qD1jPMUo80TrrGHx9JI4OnO2_2_ef52e4c2-ead5-11ea-9038-907841698cfa"),
            dict(index=3,
                 url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/GxM4qD1jPMUo80TrrGHx9JI4OnO2_3_f549d804-ead5-11ea-9038-907841698cfa"),
            dict(index=4,
                 url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/GxM4qD1jPMUo80TrrGHx9JI4OnO2_4_fc555c36-ead5-11ea-9038-907841698cfa"),
            dict(index=5,
                 url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/GxM4qD1jPMUo80TrrGHx9JI4OnO2_5_0953235a-ead6-11ea-9038-907841698cfa")
        ]
        
        array_to_dump = []
        for i in range(1, 300000):
            if i % 1000 == 0:
                print(str(100000 / i) + "%")
            
            if i % 2 == 1:
                sex = "M"
                sex_kor = "남자"
                random.shuffle(male_images)
                user_images = []
                for index, image in enumerate(male_images):
                    user_images.append(dict(index=index, url=image.get("url")))
            else:
                sex = "F"
                sex_kor = "여자"
                random.shuffle(female_images)
                user_images = []
                for index, image in enumerate(female_images):
                    user_images.append(dict(index=index, url=image.get("url")))
            
            latitude = random.randrange(33125798, 38550609) / 1000000
            longitude = random.randrange(126018599, 129576299) / 1000000
            
            user_to_insert = dict(
                uid=str(uuid.uuid1()),
                nick_name='{0} 사람_{1}'.format(sex_kor, i), sex=sex,
                birthed_at=random.randrange(495644400, 969030000),
                height=random.randrange(160, 185),
                body_id=random.randrange(1, 4),
                occupation=random.choice(["군인", "변호사", "유튜버", "연예인", "의사", "소방관", "거지"]),
                education=random.choice(["초졸", "중졸", "고졸", "전문대졸", "4년제졸", "석사", "박사"]),
                religion_id=random.randrange(0, 5),
                drink_id=random.randrange(0, 3),
                smoking_id=random.randrange(0, 3),
                blood_id=random.randrange(0, 3),
                r_token=str(uuid.uuid1()),
                latitude=latitude,
                longitude=longitude,
                location=[longitude, latitude],
                introduction='hello I am dummy user.',
                joined_at=pendulum.now().int_timestamp,
                last_login_at=pendulum.now().int_timestamp,
                user_images=user_images,
                charm_ids=[3, 4, 5, 7, 8], ideal_type_ids=[1, 5, 7, 8, 11],
                interest_ids=[3, 5, 6, 9, 13, 15])
            
            array_to_dump.append(User(**user_to_insert))
        
        User.objects.insert(array_to_dump)
    
    def test_insert_default_user(self):
        man = dict(
            uid='GxM4qD1jPMUo80TrrGHx9JI4OnO2', nick_name='mock_user_1', sex='F',
            birthed_at=1597509312, height=181, body_id=1, occupation="LAWER", education="UNIVERSITY",
            religion_id=2, drink_id=1, smoking_id=2, blood_id=1,
            r_token='cPFFTaZTQ2ivAN-bAmxNI5:APA91bFsgmm', latitude=37.5058080,
            longitude=127.0936859, introduction='hello mock_user_1', joined_at=1597509312,
            last_login_at=1597509312, user_images=[
                dict(index=0,
                     url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/GxM4qD1jPMUo80TrrGHx9JI4OnO2_0_c185da2c-ead5-11ea-9038-907841698cfa"),
                dict(index=1,
                     url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/GxM4qD1jPMUo80TrrGHx9JI4OnO2_1_e747faf6-ead5-11ea-9038-907841698cfa"),
                dict(index=2,
                     url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/GxM4qD1jPMUo80TrrGHx9JI4OnO2_2_ef52e4c2-ead5-11ea-9038-907841698cfa"),
                dict(index=3,
                     url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/GxM4qD1jPMUo80TrrGHx9JI4OnO2_3_f549d804-ead5-11ea-9038-907841698cfa"),
                dict(index=4,
                     url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/GxM4qD1jPMUo80TrrGHx9JI4OnO2_4_fc555c36-ead5-11ea-9038-907841698cfa"),
                dict(index=5,
                     url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/GxM4qD1jPMUo80TrrGHx9JI4OnO2_5_0953235a-ead6-11ea-9038-907841698cfa")
            ], charm_ids=[3, 4, 5, 7, 8, 9], ideal_type_ids=[1, 5, 7, 11, 13], interest_ids=[1, 3, 6, 13])
        
        woman = dict(
            uid='W56U9v84nfXiM842el1EWgENuzo1', nick_name='mock_user_2', sex='M',
            birthed_at=1597509312, height=181, body_id=1, occupation="LAWER", education="UNIVERSITY",
            religion_id=2, drink_id=1, smoking_id=2, blood_id=1,
            r_token='bAmxNI5:APA91bFsgmm-cPFFTaZTQ2ivAN', latitude=35.1234,
            longitude=127.987, introduction='hello mock_user_2', joined_at=1597509312,
            last_login_at=1597509312, user_images=[
                dict(index=0,
                     url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/W56U9v84nfXiM842el1EWgENuzo1_0_9280f814-ead6-11ea-9038-907841698cfa"),
                dict(index=1,
                     url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/W56U9v84nfXiM842el1EWgENuzo1_1_999790cc-ead6-11ea-9038-907841698cfa"),
                dict(index=2,
                     url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/W56U9v84nfXiM842el1EWgENuzo1_2_a3a38abc-ead6-11ea-9038-907841698cfa"),
                dict(index=3,
                     url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/W56U9v84nfXiM842el1EWgENuzo1_3_920579c2-ead7-11ea-8b30-907841698cfa"),
                dict(index=4,
                     url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/W56U9v84nfXiM842el1EWgENuzo1_4_9ae50bf2-ead7-11ea-8b30-907841698cfa"),
                dict(index=5,
                     url="https://storage.googleapis.com/pingme-280512.appspot.com/user_images/W56U9v84nfXiM842el1EWgENuzo1_5_a475a41a-ead7-11ea-8b30-907841698cfa")
            ],
            charm_ids=[6, 7, 9], ideal_type_ids=[1, 3, 9], interest_ids=[2, 3, 7])
        
        User(**man).save()
        User(**woman).save()
    
    def test_insert_an_comments(self):
        post = Post.objects.order_by("-created_at").first()
        user = User.objects.first()
        comment = Comment(
            user=user,
            comment="아무말이나 적어 놉니다 3.",
            created_at=pendulum.now().int_timestamp,
            favorite=False
        )
        comment.save()
        post.update(push__comments=comment)
        post.save()
    
    def test_insert_an_sub_comments(self):
        post = Post.objects.order_by("-created_at").first()
        user = User.objects.first()
        comment = Comment(
            user=user,
            comment="Sub comment test.",
            created_at=pendulum.now().int_timestamp,
            favorite=False
        ).save()
        post_comment = post.comments[0]
        post_comment.update(push__sub_comments=comment)
        
        post.update(push__comments=comment)
        post.save()
    
    def test_update_geo_location(self):
        user = User.objects.all()[1]
        
        alerts = Alert.objects.all()
        for alert in alerts:
            alert.delete()
        
        requests = Request.objects(user_from=user).all()
        for r in requests:
            r.delete()
        
        requests = Request.objects(user_to=user).all()
        for r in requests:
            r.delete()
        
        chat_rooms = ChatRoom.objects.all()
        for c in chat_rooms:
            c.delete()
        
        # user.update(set__location=dict(coordinates=[127.0936859, 37.505808], type='Point'))
    
    def test_insert_request(self):
        for batch in range(0, 100):
            requests = []
            print(batch)
            for i in range(0, 10000):
                result = list(User.objects.aggregate([{'$sample': {'size': 2}}]))
                user_1 = User.objects.get_or_404(id=str(result[0]["_id"]))
                user_2 = User.objects.get_or_404(id=str(result[1]["_id"]))
                requests.append(Request(
                    user_from=user_1,
                    user_to=user_2,
                    requested_at=pendulum.now().int_timestamp))
            
            Request.objects.insert(requests)
    
    def test_update_user_available(self):
        import requests
        
        user = User.objects(uid="C57KHkj5G5NVxslk3z9vxFSpIsm2").first()
        url = 'http://127.0.0.1:5000/users/{user_id}/status/approval'.format(
            user_id=str(user.id)
        )
        headers = {
            "uid": "XpazTADheYWWMEMAgTPO4nOjy4i2",
            'content-type': 'application/json'
        }
        response = requests.put(url, headers=headers)
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
