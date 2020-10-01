"""User blue print definitions."""

import pendulum
import json

from flask import Blueprint
from flask import request
from flask import Response
from model.models import User, Alert, AlertRecord

alerts_blueprint = Blueprint('alerts_blueprint', __name__)


def create_alert(user_from=None, user_to=None, push_type=None,
                 chat_room=None, post=None, comment=None,
                 _request=None, message=None):
    current_time_stamp = pendulum.now().int_timestamp
    
    if not user_to or not user_from:
        raise Exception(
            "user_from or user_to is a required value.")
    
    alert = Alert.objects(owner=user_to).first()
    
    if not alert:
        alert = Alert(owner=user_to).save()
    
    push = AlertRecord(
        push_type=push_type,
        user_id=user_from.id,
        
        post_id=post.id if post else None,
        comment_id=comment.id if comment else None,
        request_id=_request.id if _request else None,
        chat_room_id=chat_room.id if chat_room else None,
        
        message=message,
        created_at=current_time_stamp
    )
    
    alert.records = alert.records[:99]
    alert.records.append(push)
    alert.save()
    
    return alert


@alerts_blueprint.route('/alerts', methods=['GET'])
def list_alerts():
    uid = request.headers.get("uid")
    
    user = User.objects.get_or_404(uid=uid)
    
    alert = Alert.objects(owner=user).first()
    if not alert:
        alert = Alert(owner=user, records=[]).save()
    
    records = alert.records
    
    result = []
    for push in records:
        push_dict: dict = dictify_push_item(push)
        result.append(push_dict)
    
    return Response(
        json.dumps(result), mimetype='application/json')


@alerts_blueprint.route('/alerts', methods=['PUT'])
def update_all_alerts_as_read():
    uid = request.headers.get("uid")
    
    user = User.objects.get_or_404(uid=uid)
    
    alert = Alert.objects.get_or_404(owner=user)
    records = alert.records
    
    for push in records:
        push.is_read = True
    
    alert.save()
    return Response("", mimetype='application/json')


def dictify_push_item(item: AlertRecord, user=None) -> dict:
    user = user or User.objects.get_or_404(id=item.user_id)
    
    push_type = item.push_type
    nick_name = user.nick_name or ""
    user_image = next(iter(user.user_images or []), None)
    image_url = user_image.url if user_image else ""
    
    push_id = item.id
    user_id = item.user_id
    post_id = item.post_id or ""
    comment_id = item.comment_id or ""
    request_id = item.request_id or ""
    message_id = item.message_id or ""
    chat_room_id = item.chat_room_id or ""
    
    message = item.message
    created_at = str(item.created_at)
    is_read = str(item.is_read)
    
    return dict(
        push_id=str(push_id),
        user_id=str(user_id),
        post_id=str(post_id),
        comment_id=str(comment_id),
        request_id=str(request_id),
        chat_room_id=str(chat_room_id),
        message_id=str(message_id),
        
        type=push_type,
        nick_name=nick_name,
        image_url=image_url,
        message=message,
        created_at=created_at,
        is_read=is_read
    )
