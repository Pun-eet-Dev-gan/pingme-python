import json
import logging
import pendulum

from blueprints import alerts_blueprint
from flask import Blueprint
from flask import Response
from flask import request
from firebase_admin import messaging
from model.models import User, ChatRoom, Message, AlertRecord
from shared import message_service

from firebase_admin import auth

chat_rooms_blueprint = Blueprint('chat_rooms_blueprint', __name__)


@chat_rooms_blueprint.route(
    '/chat_rooms', methods=['POST'])
def test_create_chat_room():
    params = request.get_json()
    title = params.get("title", None)
    chat_room = ChatRoom(
        title=title,
        created_at=pendulum.now().int_timestamp
    ).save()
    return Response(
        chat_room.to_json(follow_reference=True, max_depth=1),
        mimetype="application/json")


@chat_rooms_blueprint.route(
    '/chat_rooms/<room_id>', methods=['DELETE'])
def test_delete_chat_room(room_id):
    chat_room = ChatRoom.objects(id=room_id).first()
    chat_room.delete()
    return Response(chat_room.to_json(
        follow_reference=True, max_depth=1),
        mimetype="application/json")


@chat_rooms_blueprint.route(
    '/chat_rooms', methods=['GET'])
def route_list_user_chat_rooms():
    uid = request.headers.get("uid", None)
    user = User.objects.get_or_404(uid=uid)
    chat_rooms = ChatRoom.objects(members=user).all()
    
    converted = []
    for chat_room in chat_rooms:
        for member in chat_room.members:
            member.uid = None
        for member in chat_room.members_history:
            member.uid = None
        converted.append(
            json.loads(chat_room.to_json(
                follow_reference=True, max_depth=2
            )))
    
    return Response(
        json.dumps(converted),
        mimetype="application/json")


@chat_rooms_blueprint.route(
    '/chat_rooms/<room_id>', methods=['GET'])
def route_get_chat_room(room_id):
    uid = request.headers.get("uid", None)
    user = User.objects.get_or_404(uid=uid)
    chat_room = ChatRoom.objects.get_or_404(id=room_id, members=user)
    return Response(chat_room.to_json(
        follow_reference=True, max_depth=1),
        mimetype="application/json")


@chat_rooms_blueprint.route(
    '/chat_rooms/<room_id>/messages/<message>', methods=['POST'])
def route_create_message(room_id: str, message: str):
    uid = request.headers.get("uid", None)
    
    user = User.objects.get_or_404(uid=uid)
    
    message = Message(
        user_id=str(user.id),
        message=message,
        created_at=pendulum.now().int_timestamp)
    
    chat_room = ChatRoom.objects.get_or_404(id=room_id, members=user)
    chat_room.messages.append(message)
    chat_room.save()
    
    user_from = user
    user_to_list = [
        member for member in chat_room.members if member.id != user.id
    ]
    
    for user_to in user_to_list:
        push = AlertRecord(
            push_type="MESSAGE",
            user_id=user_from.id,
            created_at=pendulum.now().int_timestamp,
            chat_room_id=chat_room.id,
            message_id=message.id,
            message=message.message
        )
        data = alerts_blueprint.dictify_push_item(push)
        message_service.push(data, user_to.r_token)
    
    return Response(message.to_json(), mimetype="application/json")


@chat_rooms_blueprint.route(
    '/chat_rooms/<room_id>/available/<available>', methods=['PUT'])
def route_update_chat_room_available(room_id: str, available: bool):
    id_token = request.headers.get("id_token", None)
    decoded_token = auth.verify_id_token(id_token)
    uid_to_verify = decoded_token['uid']
    uid = request.headers.get("uid", None)
    
    if uid_to_verify != uid:
        raise Exception("Illegal verify_id_token found.")
    
    chat_room = ChatRoom.objects.get_or_404(id=room_id)
    room_open_user = next((member for member in chat_room.members
                           if member.uid == uid), None)
    if not room_open_user:
        raise Exception("If not belong to the chat room, can't open it.")
    
    chat_room.available = bool(available)
    chat_room.available_at = pendulum.now().int_timestamp
    chat_room.save()
    
    for user_to in chat_room.members:
        if user_to.uid == room_open_user.uid:
            continue
        push = AlertRecord(
            push_type="OPENED",
            user_id=room_open_user.id,
            created_at=pendulum.now().int_timestamp,
            chat_room_id=chat_room.id,
            message="{nick_name} 님이 대화방을 열었습니다.".format(
                nick_name=room_open_user.nick_name)
        )
        data = alerts_blueprint.dictify_push_item(push)
        message_service.push(data, user_to.r_token)
    
    return Response(
        "", mimetype="application/json")


def send_message(chat_room_id=None, user_id=None, message=None, message_id=None,
                 registration_tokens=None, created_at=None, failed_count=0):
    if not chat_room_id or not user_id or not message_id or not registration_tokens:
        raise ValueError(
            "Invalid arguments found: chat_room_id={chat_room_id}, user_id={user_id}, "
            "message_id={message_id}, token={token}".format(
                chat_room_id=chat_room_id, user_id=user_id,
                message_id=message_id, token=registration_tokens))
    
    if failed_count > 3:
        return
    
    message = messaging.MulticastMessage(
        data=dict(
            type="MESSAGE",
            user_id=str(user_id),
            created_at=str(created_at),
            # the belows are for chatting only
            chat_room_id=str(chat_room_id),
            message_id=str(message_id),
            message=str(message)),
        tokens=registration_tokens,
        # android=messaging.AndroidConfig(priority="high"),
        apns=messaging.APNSConfig(),
        notification=messaging.Notification()
    )
    
    response = messaging.send_multicast(message)
    # cBdvpdzJSIyOVKZPsWNOGs:APA91bGNyQMxmWWgNVr3LJzM2PPnjmWtfADVaGoG0RHCiFJHFm7bd534EeoWm0REzxwxuzD5hbFbzhsQgP4557WN3m2YYOaJC3FeXCFEsmI9z8qj0Jlzm6SAaQypzCyxO4UHme0yNf5T
    if response.failure_count > 0:
        responses = response.responses
        failed_tokens = []
        for idx, resp in enumerate(responses):
            if not resp.success:
                # The order of responses corresponds to the order of the registration tokens.
                failed_tokens.append(registration_tokens[idx])
        
        logging.error('List of tokens that caused failures: %s' % failed_tokens)
