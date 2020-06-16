from flask import Blueprint, request, make_response, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity, create_refresh_token, \
    jwt_refresh_token_required, fresh_jwt_required
from helpers.database import mongo
from flask_pymongo import ObjectId
import hashlib
import random
from helpers import validation

user_bp = Blueprint("user", __name__)


@user_bp.route("/create", methods=["POST"])
def create_user():

    if not request.is_json:
        return make_response(jsonify({'message': "Missing JSON in request"}), 400)

    json = request.get_json()

    if "username" not in json or not json["username"]:
        return make_response(jsonify({"message": "Missing username parameter"}), 400)
    if "mail" not in json or not json["mail"]:
        return make_response(jsonify({"message": "Missing mail parameter"}), 400)
    if "password" not in json or not json["password"]:
        return make_response(jsonify({"message": "Missing password parameter"}), 400)

    username = json["username"]
    mail = json["mail"]
    password = json["password"]

    if not validation.validate_username(username):
        return make_response(jsonify({"message": "Illegal username"}), 400)
    if not validation.validate_mail(mail):
        return make_response(jsonify({"message": "Illegal mail"}), 400)

    password_hash = hashlib.sha512(password.encode("UTF-8")).hexdigest()

    user = {
        "username": username,
        "mail": mail,
        "password": password_hash,
        "guest": False
    }
    mongo.db.users.insert_one(user)
    return make_response(jsonify({'message': 'User created successfully'}), 201)


@user_bp.route("/guest", methods=["POST"])
def guest_user():
    while True:
        username = "guest#" + str(random.randint(0, 9999))
        if not mongo.db.users.find_one({"username": username}):
            break

    user = {
        "username": username,
        "mail": "",
        "password": "",
        "guest": True
    }
    id = mongo.db.users.insert_one(user).inserted_id

    access_token = create_access_token(identity={"_id": str(id)})
    refresh_token = create_refresh_token(identity={"_id": str(id)})

    return make_response(jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200)


@user_bp.route("/delete", methods=["DELETE"])
@jwt_required
def delete_user():
    user = get_jwt_identity()
    mongo.db.users.delete_one({"mail": user})


@user_bp.route("/login", methods=["POST"])
def login_user():

    if not request.is_json:
        return make_response(jsonify({'message': "Missing JSON in request"}), 400)

    json = request.get_json()

    if "mail" not in json or not json["mail"]:
        return make_response(jsonify({"message": "Missing mail parameter"}), 400)
    if "password" not in json or not json["password"]:
        return make_response(jsonify({"message": "Missing password parameter"}), 400)

    mail = json["mail"]
    password = json["password"]

    if not validation.validate_mail(mail):
        return make_response(jsonify({"message": "Mail is not correct"}), 400)

    password_hash = hashlib.sha512(password.encode("UTF-8")).hexdigest()

    user = mongo.db.users.find_one({"mail": mail, "password": password_hash, "guest": false})

    if not user:
        return make_response(jsonify({'message': "No matching credentials found"}), 400)

    access_token = create_access_token(identity={"_id": str(user.get("_id"))}, fresh=True)
    refresh_token = create_refresh_token(identity={"_id": str(user.get("_id"))})

    return make_response(jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200)


@user_bp.route("/refresh", methods=["POST"])
@jwt_refresh_token_required
def refresh():
    user = get_jwt_identity()
    return make_response(jsonify({"access_token": create_access_token(identity=user, fresh=False)}), 200)


@user_bp.route("/<string:_id>", methods=["GET"])
def get_username(_id):
    user = mongo.db.users.find_one({"_id": ObjectId(_id)})

    if not user:
        return make_response(jsonify({"message": "Id not found"}), 400)

    return make_response(jsonify({"username": user.get("username")}), 200)


@user_bp.route("/<string:_id>/manage", methods=["PUT"])
@fresh_jwt_required
def modify_user(_id):
    if not request.is_json:
        return make_response(jsonify({"message": "Missing JSON in request"}), 400)

    identity = get_jwt_identity()

    if not identity["_id"] == _id:
        return make_response(jsonify({"message": "Unauthorized"}), 403)

    oid = ObjectId(_id)
    json = request.get_json()

    if "username" not in json and "mail" not in json and "password" not in json:
        return make_response(jsonify({"message": "No data in JSON"}), 400)

    if "username" in json and json["username"]:
        username = json["username"]

        if not validation.validate_username(username):
            return make_response(jsonify({"message": "Illegal username"}), 400)

        mongo.db.users.update({'_id': oid}, {'$set': {'username': username}})

    if "mail" in json and json["mail"]:
        mail = json["mail"]

        if not validation.validate_mail(mail):
            return make_response(jsonify({"message": "Illegal mail"}), 400)

        mongo.db.users.update({'_id': oid}, {'$set': {'mail': mail}})

    if "password" in json and json["password"]:
        password = json["password"]

        password_hash = hashlib.sha512(password.encode("UTF-8")).hexdigest()
        mongo.db.users.update({'_id': oid}, {'$set': {'password': password_hash}})

    return make_response(jsonify({"message": "Successfully updated user"}), 200)
