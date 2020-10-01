# coding: utf-,8


import json

import flask_mongoengine as fm
import mongoengine as db
import mongoengine_goodjson as gj

from bson.objectid import ObjectId


# class Notification(gj.Document):
#     type = db.

class UserImage(gj.EmbeddedDocument):
    index = db.IntField()
    url = db.StringField()


class User(gj.Document):
    meta = {
        'queryset_class': fm.BaseQuerySet
    }
    
    uid = db.StringField()
    nick_name = db.StringField()
    sex = db.StringField()
    birthed_at = db.LongField()
    height = db.IntField()
    body_id = db.IntField()
    occupation = db.StringField()
    education = db.StringField()
    religion_id = db.IntField()
    drink_id = db.IntField()
    smoking_id = db.IntField()
    blood_id = db.IntField()
    r_token = db.StringField()
    location = db.PointField()
    introduction = db.StringField()
    joined_at = db.LongField()
    last_login_at = db.LongField()
    job = db.StringField()
    area = db.StringField()
    phone = db.StringField()
    user_images = db.SortedListField(
        db.EmbeddedDocumentField(UserImage), ordering="index"
    )
    user_images_temp = db.SortedListField(
        db.EmbeddedDocumentField(UserImage), ordering="index"
    )
    charm_ids = db.ListField(db.IntField())
    ideal_type_ids = db.ListField(db.IntField())
    interest_ids = db.ListField(db.IntField())
    
    available = db.BooleanField(default=False)
    status = db.IntField(default=0)  # -10, 0, 10
    
    @property
    def posts(self):
        posts = Post.objects(author=self).order_by(
            "-created_at").all()
        for post in posts:
            post.favorite_users = []
            post.comments.sort(
                key=lambda x: x.created_at, reverse=True)
        return posts
    
    def list_requests_like_me(self, response=None):
        return Request.objects(
            user_to=self, response=response).all()
    
    def list_requests_i_like(self, response=None):
        return Request.objects(
            user_from=self, response=response).all()
    
    def list_chat_rooms(self):
        return ChatRoom.objects(
            members=self).all()
    
    def list_users_rated_me_high(self):
        star_ratings = StarRating.objects(
            user_to=self, score__gte=4).all()
        return [
            star_rating.user_from for star_rating in star_ratings
        ]


class Comment(gj.Document):
    meta = {
        'queryset_class': fm.BaseQuerySet
    }
    user = db.ReferenceField(
        User, required=True, reverse_delete_rule=db.CASCADE)
    comment = db.StringField()
    sub_comments = db.ListField(
        db.ReferenceField('self'),
        reverse_delete_rule=db.CASCADE)
    created_at = db.LongField(required=True)
    thumb_up_user_ids = db.ListField(db.ObjectIdField())
    thumb_down_user_ids = db.ListField(db.ObjectIdField())


class Post(gj.Document):
    meta = {
        'queryset_class': fm.BaseQuerySet
    }
    author = db.ReferenceField(
        User, required=True, reverse_delete_rule=db.CASCADE)
    title = db.StringField()
    description = db.StringField()
    url = db.StringField()
    favorite_user_ids = db.ListField(db.ObjectIdField())
    favorite_users = db.ListField(
        db.ReferenceField(
            User, reverse_delete_rule=db.CASCADE))
    comments = db.ListField(
        db.ReferenceField(
            Comment, reverse_delete_rule=db.CASCADE))
    created_at = db.LongField(required=True)
    enable_comment = db.BooleanField()
    is_deleted = db.BooleanField()


class Request(gj.Document):
    meta = {
        'queryset_class': fm.BaseQuerySet
    }
    user_from = db.ReferenceField(
        User, required=True, reverse_delete_rule=db.CASCADE)
    user_to = db.ReferenceField(
        User, required=True, reverse_delete_rule=db.CASCADE)
    requested_at = db.LongField()
    request_type_id = db.IntField(required=True)
    response = db.IntField()
    responded_at = db.LongField()


class StarRating(gj.Document):
    meta = {
        'queryset_class': fm.BaseQuerySet
    }
    user_from = db.ReferenceField(
        User, required=True, reverse_delete_rule=db.CASCADE)
    user_to = db.ReferenceField(
        User, required=True, reverse_delete_rule=db.CASCADE)
    rated_at = db.LongField(required=True)
    score = db.IntField(required=True)


class Message(gj.EmbeddedDocument):
    meta = {
        'queryset_class': fm.BaseQuerySet
    }
    id = db.ObjectIdField(
        required=True, default=lambda: ObjectId())
    user_id = db.ObjectIdField()
    message = db.StringField()
    created_at = db.LongField(required=True)


class ChatRoom(gj.Document):
    meta = {
        'queryset_class': fm.BaseQuerySet
    }
    title = db.StringField(max_length=500)
    members = db.SortedListField(
        db.ReferenceField(User), reverse_delete_rule=db.CASCADE)
    members_history = db.ListField(
        db.ReferenceField(User), reverse_delete_rule=db.CASCADE)
    messages = db.EmbeddedDocumentListField(Message)
    created_at = db.LongField(required=True)
    available = db.BooleanField(required=True, default=False)
    available_at = db.LongField()


class AlertRecord(gj.EmbeddedDocument):
    id = db.ObjectIdField(
        required=True, default=lambda: ObjectId())
    push_type = db.StringField(
        required=True)
    user_id = db.ObjectIdField()
    post_id = db.ObjectIdField()
    comment_id = db.ObjectIdField()
    request_id = db.ObjectIdField()
    chat_room_id = db.ObjectIdField()
    message_id = db.ObjectIdField()  # ChatRoom@Message
    message = db.StringField()
    created_at = db.LongField(required=True)
    is_read = db.BooleanField()


class Alert(gj.Document):
    meta = {
        'queryset_class': fm.BaseQuerySet
    }
    owner = db.ReferenceField(
        User, reverse_delete_rule=db.CASCADE)
    records = db.SortedListField(
        db.EmbeddedDocumentField(AlertRecord),
        ordering="created_at", reverse=True
    )
