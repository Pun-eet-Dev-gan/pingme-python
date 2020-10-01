import json
import uuid
import pendulum

from blueprints import alerts_blueprint
from flask import abort
from flask import Blueprint
from flask import Response
from flask import request
from firebase_admin import storage
from model.models import User, Post, Comment
from shared import message_service

posts_blueprint = Blueprint('posts_blueprint', __name__)


@posts_blueprint.route(
    '/posts', methods=['POST'])
def route_create_post():
    uid = request.headers.get("uid", None)
    if not uid:
        abort(401)
    
    params = request.form.to_dict(flat=True)
    post_image = request.files.get("post_image", None)
    description = params.get("description", None)
    title = params.get("title", None)
    enable_comment = params.get("enable_comment", 'false')
    enable_comment = True if enable_comment == "true" else False
    
    user = User.objects(uid=uid).get_or_404()
    
    url = None
    if post_image:
        # update to image server
        bucket = storage.bucket()
        blob = bucket.blob(
            'post_images/{uid}/{uuid}_{timestamp}'.format(
                uid=uid, uuid=uuid.uuid1(),
                timestamp=pendulum.now().int_timestamp))
        blob.upload_from_file(post_image)
        url = blob.public_url
    
    if not post_image and not params.get("description", ""):
        raise ValueError(
            "이미지 및 게시글 중 최소 한개는 충족 되어야 합니다.")
    
    # create a post in mongo db.
    post = Post(author=user,
                title=title,
                description=description,
                url=url,
                created_at=pendulum.now().int_timestamp,
                enable_comment=enable_comment)
    post.save()
    
    return Response(post.to_json(
        follow_reference=True, max_depth=1),
        mimetype="application/json")


@posts_blueprint.route(
    '/posts', methods=['GET'])
def route_list_posts():
    page: int = int(request.args.get("page", 0))
    per_page: int = int(request.args.get("per_page", 30))
    
    skip = page * per_page if page > 0 else 0
    limit = (page + 1) * per_page
    
    posts = Post.objects.order_by(
        "-created_at").skip(skip).limit(limit).all()
    
    converted = []
    for post in posts:
        post.favorite_users = []
        post.comments.sort(
            key=lambda x: x.created_at, reverse=True)
        converted.append(json.loads(post.to_json(
            follow_reference=True, max_depth=3
        )))
    
    return Response(
        json.dumps(converted),
        mimetype="application/json")


@posts_blueprint.route(
    '/posts/<post_id>', methods=['GET'])
def route_get_post(post_id):
    post = Post.objects.get_or_404(id=post_id)
    post.comments.sort(
        key=lambda x: x.created_at, reverse=True)
    return Response(post.to_json(
        follow_reference=True, max_depth=3),
        mimetype="application/json")


@posts_blueprint.route(
    '/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    post = Post.objects.get_or_404(id=post_id)
    post.delete()
    return Response(
        json.dumps(dict(id=str(post.id))),
        mimetype="application/json")


@posts_blueprint.route(
    '/posts/<post_id>/favorite', methods=['POST'])
def route_create_favorite(post_id: str):
    uid = request.headers.get("uid", None)
    if not uid:
        abort(401)
    
    user = User.objects.get_or_404(uid=uid)
    post = Post.objects.get_or_404(id=post_id)
    post.update(add_to_set__favorite_users=user,
                add_to_set__favorite_user_ids=user.id)
    
    user_from = user
    user_to = post.author
    
    alert = alerts_blueprint.create_alert(
        user_from=user_from, user_to=user_to,
        push_type="FAVORITE", post=post,
        message="{nick_name} 님이 당신의 게시물을 좋아합니다.".format(
            nick_name=user_from.nick_name))
    push_item = alert.records[-1]
    data = alerts_blueprint.dictify_push_item(push_item)
    message_service.push(data, user_to.r_token)
    
    return Response(post.to_json(
        follow_reference=True, max_depth=1),
        mimetype="application/json")


@posts_blueprint.route(
    '/posts/<post_id>/favorite', methods=['DELETE'])
def route_delete_favorite(post_id):
    uid = request.headers.get("uid", None)
    if not uid:
        abort(401)
    
    user = User.objects.get_or_404(uid=uid)
    post = Post.objects.get_or_404(id=post_id)
    
    post.update(pull__favorite_users=user,
                pull__favorite_user_ids=user.id)
    
    return Response(post.to_json(
        follow_reference=True, max_depth=1),
        mimetype="application/json")


@posts_blueprint.route(
    '/posts/<post_id>/comment', methods=['POST'])
def route_create_comment(post_id: str):
    uid = request.headers.get("uid", None)
    if not uid:
        abort(401)
    
    # if exists, create a comment as a sub comment
    comment_id = request.form.get("comment_id", None)
    comment = request.form.get("comment", "")
    
    post = Post.objects.get_or_404(id=post_id)
    user = User.objects.get_or_404(uid=uid)
    
    comment_to_create = Comment(
        user=user,
        comment=comment,
        sub_comments=[],
        created_at=pendulum.now().int_timestamp
    ).save()
    
    if comment_id:
        comment = next((comment for comment in post.comments
                        if str(comment.id) == comment_id), None)
        if not comment:
            raise ValueError("Not found an appropriate comment.")
        
        comment_to_update = Comment.objects.get_or_404(
            id=comment_id)
        comment_to_update.update(
            push__sub_comments=comment_to_create)
    else:
        post.update(
            push__comments=comment_to_create)
    
    return Response(comment_to_create.to_json(
        follow_reference=True, max_depth=1),
        mimetype="application/json")


@posts_blueprint.route(
    '/posts/<post_id>/comments/<comment_id>/thumb_up', methods=['POST'])
def route_create_thumb_up(post_id, comment_id):
    uid = request.headers.get("uid", None)
    if not uid:
        abort(401)
    
    user = User.objects.get_or_404(uid=uid)
    post = Post.objects.get_or_404(id=post_id)
    comment = next(
        (comment for comment in post.comments
         if str(comment.id) == comment_id), None)
    
    if not comment:
        abort(404)
    
    comment.update(
        add_to_set__thumb_up_user_ids=user.id,
        pull__thumb_down_user_ids=user.id)
    comment = Comment.objects.get_or_404(id=comment_id)
    
    if user.id == post.author.id:
        user_from = user
        user_to = comment.user
        
        alert = alerts_blueprint.create_alert(
            user_from=user_from, user_to=user_to,
            push_type="THUMB_UP",
            post=post, comment=comment,
            message="{nick_name} 님이 당신의 댓글을 좋아합니다.".format(
                nick_name=user_from.nick_name))
        push_item = alert.records[-1]
        data = alerts_blueprint.dictify_push_item(push_item)
        message_service.push(data, user_to.r_token)
    
    return Response(comment.to_json(
        follow_reference=True, max_depth=2),
        mimetype="application/json")


@posts_blueprint.route(
    '/posts/<post_id>/comments/<comment_id>/thumb_up', methods=['DELETE'])
def route_delete_thumb_up(post_id, comment_id):
    uid = request.headers.get("uid", None)
    if not uid:
        abort(401)
    
    user = User.objects.get_or_404(uid=uid)
    post = Post.objects.get_or_404(id=post_id)
    comment = next(
        (comment for comment in post.comments
         if str(comment.id) == comment_id), None)
    
    comment.update(pull__thumb_up_user_ids=user.id)
    comment = Comment.objects.get_or_404(id=comment_id)
    
    return Response(comment.to_json(
        follow_reference=True, max_depth=2),
        mimetype="application/json")


@posts_blueprint.route(
    '/posts/<post_id>/comments/<comment_id>/thumb_down', methods=['POST'])
def route_create_thumb_down(post_id, comment_id):
    uid = request.headers.get("uid", None)
    if not uid:
        abort(401)
    
    user = User.objects.get_or_404(uid=uid)
    post = Post.objects.get_or_404(id=post_id)
    comment = next(
        (comment for comment in post.comments
         if str(comment.id) == comment_id), None)
    
    comment.update(
        add_to_set__thumb_down_user_ids=user.id,
        pull__thumb_up_user_ids=user.id)
    comment = Comment.objects.get_or_404(id=comment_id)
    
    return Response(comment.to_json(
        follow_reference=True, max_depth=2),
        mimetype="application/json")


@posts_blueprint.route(
    '/posts/<post_id>/comments/<comment_id>/thumb_down', methods=['DELETE'])
def route_delete_thumb_down(post_id, comment_id):
    uid = request.headers.get("uid", None)
    if not uid:
        abort(401)
    
    user = User.objects.get_or_404(uid=uid)
    post = Post.objects.get_or_404(id=post_id)
    comment = next(
        (comment for comment in post.comments
         if str(comment.id) == comment_id), None)
    
    comment.update(pull__thumb_down_user_ids=user.id)
    comment = Comment.objects.get_or_404(id=comment_id)
    
    return Response(comment.to_json(
        follow_reference=True, max_depth=2),
        mimetype="application/json")


@posts_blueprint.route(
    '/posts/<post_id>/favorite', methods=['GET'])
def route_list_all_favorite_users(post_id):
    uid = request.headers.get("uid", None)
    post = Post.objects.get_or_404(id=post_id)
    
    if post.author.uid != uid:
        abort(401)
    
    users = post.favorite_users
    
    converted = []
    for user in users:
        user.uid = None
        converted.append(json.loads(user.to_json(
            follow_reference=True, max_depth=1
        )))
    
    return Response(
        json.dumps(converted),
        mimetype="application/json")
