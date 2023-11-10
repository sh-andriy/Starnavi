from datetime import datetime
from operator import and_

from flask import Blueprint, request, jsonify
from sqlalchemy import func

from .models import Post, Like, User
from . import db
from flask_jwt_extended import jwt_required, get_jwt_identity

post_blueprint = Blueprint('post', __name__, url_prefix='/api')


@post_blueprint.route('/post', methods=['POST'])
@jwt_required()
def create_post():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    content = request.json.get('content', None)
    if not content:
        return jsonify({"msg": "Content is required"}), 400

    post = Post(content=content, author=user)
    user.last_request_at = datetime.utcnow()

    db.session.add(post)
    db.session.commit()
    return jsonify({"post_id": post.id, "content": post.content,
                   "user_email": user.email}), 201


@post_blueprint.route('/post/<int:post_id>/like', methods=['POST'])
@jwt_required()
def like_post(post_id):
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    post = Post.query.get_or_404(post_id)
    if Like.query.filter_by(user_id=user.id, post_id=post_id).first():
        return jsonify({"msg": "Post already liked"}), 409

    like = Like(user_id=user.id, post_id=post.id)
    user.last_request_at = datetime.utcnow()

    db.session.add(like)
    db.session.commit()
    return jsonify({"msg": "Post liked"}), 200


@post_blueprint.route('/post/<int:post_id>/unlike', methods=['POST'])
@jwt_required()
def unlike_post(post_id):
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    like = Like.query.filter_by(user_id=user.id, post_id=post_id).first()
    if not like:
        return jsonify({"msg": "Like does not exist"}), 404

    user.last_request_at = datetime.utcnow()

    db.session.delete(like)
    db.session.commit()
    return jsonify({"msg": "Post unliked"}), 200


@post_blueprint.route('/analytics/', methods=['GET'])
@jwt_required()
def analytics():
    date_from = request.args.get('date_from', None)
    date_to = request.args.get('date_to', None)

    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
        except ValueError:
            return jsonify(
                {"msg": "Incorrect date_from format, should be YYYY-MM-DD"}), 400
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
        except ValueError:
            return jsonify(
                {"msg": "Incorrect date_to format, should be YYYY-MM-DD"}), 400

    if date_from and not date_to:
        date_to = datetime.utcnow()

    if date_to and not date_from:
        date_from = datetime.min

    # Adjust date_to to include the entire day
    if date_to:
        date_to = datetime(
            date_to.year,
            date_to.month,
            date_to.day,
            23,
            59,
            59)

    like_counts_query = db.session.query(
        func.date(Like.created_at).label('date'),
        func.count('*').label('likes')
    )

    if date_from and date_to:
        like_counts_query = like_counts_query.filter(
            and_(Like.created_at >= date_from, Like.created_at <= date_to)
        )
    elif date_from:
        like_counts_query = like_counts_query.filter(
            Like.created_at >= date_from)
    elif date_to:
        like_counts_query = like_counts_query.filter(
            Like.created_at <= date_to)

    like_counts = like_counts_query.group_by(func.date(Like.created_at)).all()

    analytics_data = [
        {"date": str(result.date), "likes": result.likes} for result in like_counts
    ]

    return jsonify(analytics_data), 200


@post_blueprint.route('/activity', methods=['GET'])
@jwt_required()
def user_activity():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    last_login_at = user.last_login_at
    last_request_at = user.last_request_at
    return jsonify({
        "last_login_at": last_login_at,
        "last_request_at": last_request_at
    }), 200
