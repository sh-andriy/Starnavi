import re

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    create_refresh_token,
)
from .models import User
from . import db

auth_blueprint = Blueprint('auth', __name__, url_prefix='/api')

# Regular expression for validating an Email
regex = r'^[a-z0-9]+[\._-]?[a-z0-9]+[@]\w+[.]\w+$'


@auth_blueprint.route('/signup', methods=['POST'])
def signup():
    email = request.json.get('email', None)
    password = request.json.get('password', None)

    # Validate email format
    if not re.match(regex, email):
        return jsonify({"msg": "Invalid email format"}), 400

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already registered"}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    if new_user:
        # Create tokens for the new registration
        access_token = create_access_token(identity=new_user.email)
        refresh_token = create_refresh_token(identity=new_user.email)

        return jsonify({
            "msg": "User created successfully",
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 201
    else:
        return jsonify({"msg": "Failed to create user"}), 500


@auth_blueprint.route('/login', methods=['POST'])
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400
    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=email)
        refresh_token = create_refresh_token(identity=email)
        return jsonify(access_token=access_token,
                       refresh_token=refresh_token), 200
    else:
        return jsonify({"msg": "Invalid login credentials"}), 401


@auth_blueprint.route('/token/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return jsonify(access_token=new_access_token), 200
