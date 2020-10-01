"""User blue print definitions."""

import hashlib
import json
import logging
import pendulum
import urllib3
import uuid
import random
import re

from blueprints import alerts_blueprint

from flask import abort
from flask import Blueprint
from flask import request
from flask import Response

from firebase_admin import messaging
from firebase_admin import storage
from firebase_admin import auth

from model.models import User, UserImage, ChatRoom, Alert, Request, StarRating
from shared import message_service

users_blueprint = Blueprint("users_blueprint", __name__)

IMAGE_MIMETYPE_REGEX = r"image/.*"

USER_IMAGE_FOLDER = "user_images"

OPENED = 0
PENDING = 10
APPROVED = 20
REJECTED = -10

http = urllib3.PoolManager()

ACCESS_KEY = "e8ab27ee174997778b7826a94b7db233"


def get_coordinates_by_ip(req):
    try:
        ip_address = req.remote_addr
        response = http.request(
            "GET", "http://api.ipstack.com/{ip_address}?access_key={access_key}".format(
                ip_address=ip_address, access_key=ACCESS_KEY))
        value = json.loads(response.data.decode('utf8'))
        longitude, latitude = value.get("longitude"), value.get("latitude")
        return float(longitude), float(latitude)
    except Exception as e:
        return None, None


@users_blueprint.route("/users", methods=["POST"])
def create_user():
    id_token = request.headers.get("id_token", None)
    decoded_token = auth.verify_id_token(id_token)
    uid_to_verify = decoded_token['uid']
    uid = request.headers.get("uid", None)
    
    if uid_to_verify != uid:
        raise Exception("Illegal verify_id_token found.")
    
    user = User.objects(uid=uid).first()
    
    if not user:
        user = User(
            uid=uid, status=OPENED, available=False).save()
        Alert(owner=user, records=[]).save()
    
    return Response(
        user.to_json(),
        mimetype="application/json")


@users_blueprint.route("/users/location", methods=["PUT"])
def update_user_location():
    uid = request.headers.get("uid")
    user = User.objects.get_or_404(uid=uid)
    
    longitude, latitude = \
        request.args.get("longitude", None), request.args.get("latitude", None)
    
    if not longitude or not latitude:
        longitude, latitude = get_coordinates_by_ip(request)
    
    if not longitude or not latitude:
        return Response(
            json.dumps(dict(coordinates=[], type="Point")),
            mimetype="application/json")
    
    coordinates = [float(longitude), float(latitude)]
    user.update(**dict(location=coordinates))
    
    return Response(
        json.dumps(dict(coordinates=coordinates, type="Point")),
        mimetype="application/json")


@users_blueprint.route("/users/profile", methods=["PUT"])
def update_user_profile():
    def is_two_dimensional(location):
        if not location:
            return False
        if not location.get("coordinates", None):
            return False
        if len(location.get("coordinates")) != 2:
            return False
        return True
    
    uid = request.headers.get("uid")
    user_json = request.get_json()
    prohibited = [
        "uid",
        "user_ids_i_sent_request",
        "user_ids_matched",
        "user_ids_sent_me_request",
        "star_ratings_i_rated",
        "user_images",
        "location",
        "r_token"
    ]
    for p in prohibited:
        user_json.pop(p, None)
    
    required_strip = ["nick_name", "occupation", "education"]
    for r in required_strip:
        value = user_json.get(r, None)
        if value is None:
            raise ValueError(
                "{0} is required value.".format(value))
        value = value.strip()
        user_json[r] = value
    
    user = User.objects.get_or_404(uid=uid)
    user.update(**user_json)
    user = User.objects(uid=uid).get_or_404()
    return Response(
        user.to_json(),
        mimetype="application/json")


@users_blueprint.route("/users", methods=["GET"])
def list_users():
    """Endpoint for getting users."""
    users = User.objects.all()[:4]
    converted = []
    for user in users:
        user.uid = None
        converted.append(json.loads(user.to_json(
            follow_reference=True, max_depth=1
        )))
    return Response(
        json.dumps(converted),
        mimetype="application/json")


@users_blueprint.route("/users/<user_id>/rated_me_high", methods=["GET"])
def route_list_users_rated_me_high(user_id: str):
    uid = request.headers.get("uid")
    user = User.objects.get_or_404(uid=uid)
    
    if str(user.id) != user_id:
        raise abort(401)
    
    users = user.list_users_rated_me_high()
    
    converted = []
    for user in users:
        user.uid = None
        converted.append(json.loads(user.to_json(
            follow_reference=True, max_depth=1
        )))
    
    return Response(
        json.dumps(converted),
        mimetype="application/json")


@users_blueprint.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    """Endpoint for getting user."""
    user = User.objects.get_or_404(id=user_id)
    return Response(
        user.to_json(),
        mimetype="application/json")


@users_blueprint.route("/users/session", methods=["GET"])
def get_session():
    uid = request.headers.get("uid", None)
    """Endpoint for getting user session."""
    user_session = User.objects.get_or_404(uid=uid)
    
    star_rating = StarRating.objects(user_from=user_session).all()
    
    received = Request.objects(user_to=user_session).all()
    sent = Request.objects(user_from=user_session).all()
    
    user_ids_matched = [str(s.user_to.id) for s in sent if s.response == 1] + [
        str(r.user_from.id) for r in received if r.response == 1]
    user_ids_i_sent_request = [str(s.user_to.id) for s in sent if s.response != 1]
    user_ids_sent_me_request = [str(r.user_from.id) for r in received if r.response != 1]
    user_ids_i_rated = [
        dict(user_id=str(rate.user_to.id), score=rate.score) for rate in star_rating]
    
    user_session = json.loads(user_session.to_json())
    user_session["user_ids_matched"] = user_ids_matched
    user_session["user_ids_i_sent_request"] = user_ids_i_sent_request
    user_session["user_ids_sent_me_request"] = user_ids_sent_me_request
    user_session["star_ratings_i_rated"] = user_ids_i_rated
    
    return Response(
        json.dumps(user_session),
        mimetype="application/json")


@users_blueprint.route(
    "/users/r_token/<r_token>", methods=["PUT"])
def route_update_registration_token(r_token: str):
    """Endpoint for updating user registration token."""
    uid = request.headers.get("uid", None)
    user = User.objects.get_or_404(uid=uid)
    user.r_token = r_token
    user.save()
    
    return Response(
        user.to_json(),
        mimetype="application/json")


@users_blueprint.route(
    "/users/user_images/<int:index>", methods=["POST", "PUT"])
def route_upload_user_image(index: int):
    """Endpoint for uploading profile images."""
    uid = request.headers.get("uid", None)
    image_file = request.files["file"]
    
    user = User.objects.get_or_404(uid=uid)
    
    if not re.match(IMAGE_MIMETYPE_REGEX, image_file.mimetype):
        raise ValueError("The file is not an image type.")
    
    bucket = storage.bucket()
    file_name_to_save = "{0}_{1}_{2}".format(
        uid, index, uuid.uuid1())
    blob = bucket.blob(
        "{0}/{1}".format(
            USER_IMAGE_FOLDER, file_name_to_save))
    blob.upload_from_file(image_file)
    
    user_images_temp = user.user_images_temp
    current_image_at_index = next(
        (x for x in user_images_temp if x.index == index), None)
    
    if not current_image_at_index:  # create new one
        user.user_images_temp.append(
            UserImage(index=index, url=blob.public_url))
    else:  # update existing one
        current_image_at_index.url = blob.public_url
    user.status = OPENED
    user.save()
    
    updated_image = next(
        (x for x in user_images_temp if x.index == index), None)
    
    return Response(
        updated_image.to_json(),
        mimetype="application/json")


@users_blueprint.route(
    "/users/<user_id>/status/approval", methods=["PUT"])
def route_update_user_status_to_approved(user_id: str):
    """Endpoint for updating user status."""
    user = User.objects.get_or_404(id=user_id)
    
    user.user_images = user.user_images_temp
    
    user.status = APPROVED
    user.available = True
    user.save()
    
    return Response(
        user.to_json(),
        mimetype="application/json")


@users_blueprint.route(
    "/users/<user_id>/status/rejection", methods=["PUT"])
def route_update_user_status_to_rejected(user_id: str):
    """Endpoint for updating user status."""
    user = User.objects.get_or_404(id=user_id)
    
    user.user_images = user.user_images_temp
    user.status = REJECTED
    user.save()
    
    return Response(
        user.to_json(),
        mimetype="application/json")


@users_blueprint.route("/users/<user_id>/status/pending", methods=["PUT"])
def route_update_user_status_pending(user_id: str):
    uid = request.headers.get("uid")
    user = User.objects.get_or_404(uid=uid)
    
    if str(user.id) != user_id:
        raise abort(401)
    
    user.status = PENDING
    user.save()
    
    return Response(user.to_json(), mimetype="application/json")


@users_blueprint.route(
    "/users/user_images/<int:index>", methods=["DELETE"])
def route_delete_user_image(index: int):
    uid = request.headers.get("uid", None)
    user = User.objects.get_or_404(uid=uid)
    
    user_image_to_remove = next(
        (user_image_temp for user_image_temp in user.user_images_temp
         if user_image_temp.index == index), None)
    
    user.update(pull__user_images_temp=user_image_to_remove)
    user.status = OPENED
    user.save()
    user = User.objects.get_or_404(uid=uid)
    
    return Response(
        user.to_json(), mimetype="application/json")


@users_blueprint.route("/users/<user_id>/posts", methods=["GET"])
def route_list_user_posts(user_id):
    user = User.objects.get_or_404(id=user_id)
    posts = user.posts()
    
    converted = []
    for post in posts:
        converted.append(json.loads(post.to_json(
            follow_reference=True, max_depth=3)))
    
    return Response(
        json.dumps(converted),
        mimetype="application/json")


@users_blueprint.route("/users/<uid>/chat_rooms", methods=["GET"])
def route_list_chat_rooms(uid: str):
    chat_rooms = ChatRoom.objects(
        members=User.objects(uid=uid).first())
    
    return Response(json.dumps(
        [json.loads(chat_room.to_json(
            follow_reference=True, max_depth=1))
            for chat_room in chat_rooms]),
        mimetype="application/json")


@users_blueprint.route(
    "/users/poke/<user_id_to>", methods=["POST"])
def route_poke(user_id_to):
    uid = request.headers.get("uid", None)
    
    user_from = User.objects(uid=uid).get_or_404()
    
    user_to = User.objects(id=user_id_to).get_or_404()
    
    alert = alerts_blueprint.create_alert(
        user_from, user_to, push_type="POKE",
        message="{nick_name} 님이 당신을 찔렀습니다.".format(
            nick_name=user_from.nick_name))
    push_item = alert.records[-1]
    data: dict = alerts_blueprint.dictify_push_item(push_item)
    
    try:
        message = messaging.Message(
            data=data, token=user_to.r_token,
            apns=messaging.APNSConfig(),
            android=messaging.AndroidConfig(priority="high"),
            notification=messaging.Notification())
        messaging.send(message)
    except Exception as e:
        logging.exception(e)
    
    return Response(
        user_to.to_json(),
        mimetype="application/json")


@users_blueprint.route("/users/real_time", methods=["GET"])
def list_users_real_time():
    """Endpoint for getting users."""
    uid = request.headers.get("uid", None)
    
    user = User.objects.get_or_404(uid=uid)
    
    users = User.objects(
        location__near=user.location["coordinates"],
        location__max_distance=30 * 1000  # 20 km
    ).order_by("-last_login_at").limit(5).all()
    
    converted = []
    for user in users:
        user.uid = None
        converted.append(json.loads(user.to_json(
            follow_reference=True, max_depth=1
        )))
    return Response(
        json.dumps(converted),
        mimetype="application/json")


@users_blueprint.route("/users/close", methods=["GET"])
def list_users_close():
    """Endpoint for getting users."""
    uid = request.headers.get("uid", None)
    
    user_session = User.objects.get_or_404(uid=uid)
    
    users = User.objects(
        location__near=user_session.location["coordinates"],
        location__max_distance=5 * 1000  # 5 km
    ).all()
    
    user_ids = [user.id for user in users]
    
    random.seed(get_hash(uid) + 1)
    random.shuffle(user_ids)
    
    selected_users = User.objects(
        id__in=user_ids[:4]).all()
    
    converted = []
    for selected_user in selected_users[:4]:
        selected_user.uid = None
        converted.append(
            json.loads(selected_user.to_json(
                follow_reference=True, max_depth=1
            )))
    return Response(
        json.dumps(converted),
        mimetype="application/json")


@users_blueprint.route(
    "/users/<user_id>/score/<int:score>", methods=["PUT"])
def route_update_star_rating(user_id: str, score: int):
    """Endpoint for getting users."""
    uid = request.headers.get("uid", None)
    
    user_from = User.objects.get_or_404(uid=uid)
    user_to = User.objects.get_or_404(id=user_id)
    
    past_star_rating = StarRating.objects(
        user_from=user_from, user_to=user_to).first()
    
    if not past_star_rating:
        StarRating(
            user_from=user_from, user_to=user_to,
            rated_at=pendulum.now().int_timestamp,
            score=score
        ).save()
        if score > 3:
            alert = alerts_blueprint.create_alert(
                user_from=user_from, user_to=user_to,
                push_type="STAR_RATING",
                message="{nick_name} 님이 당신을 높게 평가 하였습니다.".format(
                    nick_name=user_from.nick_name))
            push_item = alert.records[-1]
            data = alerts_blueprint.dictify_push_item(push_item)
            message_service.push(data, user_to.r_token)
    
    return Response("", mimetype="application/json")


def get_hash(user_id: str):
    today = str(pendulum.yesterday().date())
    hash_today = int(
        hashlib.sha1(
            today.encode("utf-8")).hexdigest(), 16) % 10 ** 8
    user_own_hash = int(
        hashlib.sha1(
            user_id.encode("utf-8")).hexdigest(), 16) % 10 ** 8
    return hash_today + user_own_hash
