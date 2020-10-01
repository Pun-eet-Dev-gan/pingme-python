"""Request blue print definitions."""

import json
import logging
import pendulum

from blueprints import alerts_blueprint
from flask import abort
from flask import Blueprint
from flask import Response
from flask import request
from firebase_admin import auth
from model.models import Request, User, ChatRoom
from shared import message_service

requests_blueprint = Blueprint("requests_blueprint", __name__)


@requests_blueprint.route(
    "/requests", methods=["GET"])
def route_list_requests_to_me():
    """Endpoint for like request list."""
    uid = request.headers.get("uid", None)
    user = User.objects(uid=uid).first()
    requests = user.list_requests_like_me()
    return Response(
        json.dumps([json.loads(req.to_json(
            follow_reference=True, max_depth=1
        )) for req in requests]),
        mimetype="application/json")


@requests_blueprint.route(
    "/requests/<request_id>", methods=["GET"])
def route_get_requests_to_me(request_id: str):
    """Endpoint for like request list."""
    uid = request.headers.get("uid", None)
    user = User.objects(uid=uid).get_or_404()
    
    _request = Request.objects.get_or_404(user_to=user, id=request_id)
    _request.user_to.uid = None
    _request.user_from.uid = None
    
    return Response(
        _request.to_json(follow_reference=True, max_depth=1),
        mimetype="application/json"
    )


@requests_blueprint.route(
    "/requests/user_to/<user_id>/type/<int:r_type>", methods=["POST"])
def route_create_request(user_id: str, r_type: int):
    """Endpoint to request like."""
    id_token = request.headers.get("id_token", None)
    decoded_token = auth.verify_id_token(id_token)
    uid_to_verify = decoded_token["uid"]
    uid = request.headers.get("uid", None)
    
    if uid_to_verify != uid:
        raise Exception("Illegal verify_id_token found.")
    
    user_from = User.objects.get_or_404(uid=uid)  # me
    user_to = User.objects.get_or_404(id=user_id)  # target
    
    # checks if there is a one I have already sent
    request_i_sent = Request.objects(
        user_to=user_to,  # target
        user_from=user_from  # me
    ).first()
    
    if request_i_sent:
        raise ValueError(
            "a duplicate request already exists.")
    
    # checks if there is a one I have received.
    request_i_received = Request.objects(
        user_to=user_from, user_from=user_to).first()
    
    if request_i_received:
        if request_i_received.response == None:
            return route_update_response_of_request(
                request_i_received.id, 1)
        else:
            raise ValueError(
                "a duplicate request already exists.")
    
    _request = Request(
        user_from=user_from, user_to=user_to,
        request_type_id=r_type,
        requested_at=pendulum.now().int_timestamp,
        response=None, responded_at=None)
    _request.save()
    
    alert = alerts_blueprint.create_alert(
        user_from=user_from, user_to=user_to,
        push_type="REQUEST", _request=_request,
        message="{nick_name} 님이 당신에게 친구 신청을 보냈습니다.".format(
            nick_name=user_from.nick_name))
    push_item = alert.records[-1]
    data = alerts_blueprint.dictify_push_item(push_item)
    message_service.push(data, user_to.r_token)
    
    return Response(
        _request.to_json(follow_reference=True, max_depth=1),
        mimetype="application/json")


@requests_blueprint.route(
    "/requests/<rid>/response/<int:result>", methods=["PUT"])
def route_update_response_of_request(rid: str, result: int):
    """Updates a received like request.
       ACCEPT: 1
       DECLINE: 0
    """
    
    uid = request.headers.get("uid", None)
    me = User.objects.get_or_404(uid=uid)
    
    _request = Request.objects(id=rid).get_or_404()
    
    if _request.user_to.id != me.id:
        abort(400)
    
    # update request table.
    _request.response = result
    _request.responded_at = pendulum.now().int_timestamp
    _request.save()
    
    if int(result) == 1:
        # create chat room
        chat_room = ChatRoom(
            title=None,
            members=[_request.user_from, _request.user_to],
            members_history=[_request.user_from, _request.user_to],
            created_at=pendulum.now().int_timestamp)
        chat_room.save()
        
        # watch out here..
        user_from = _request.user_to
        user_to = _request.user_from
        
        alert = alerts_blueprint.create_alert(
            user_from=user_from, user_to=user_to,
            push_type="MATCHED", _request=_request, chat_room=chat_room,
            message="{nick_name} 님과 연결 되었습니다.".format(
                nick_name=_request.user_to.nick_name))
        push_item = alert.records[-1]
        data = alerts_blueprint.dictify_push_item(push_item)
        message_service.push(data, user_to.r_token)
    
    return Response(
        _request.to_json(follow_reference=True, max_depth=1),
        mimetype="application/json")
