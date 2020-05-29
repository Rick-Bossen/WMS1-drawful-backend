from flask import Blueprint, request, make_response, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity, create_refresh_token, \
    jwt_refresh_token_required, fresh_jwt_required
from jwt_global import jwt
from database import mongo
from flask_pymongo import ObjectId
import hashlib

user_bp = Blueprint("user", __name__)


@user_bp.route("/create", methods=["POST"])
def create_user():
    # TODO add validation

    if not request.is_json:
        return make_response(jsonify({'message': "Missing JSON in request"}), 400)

    json = request.get_json()

    username = json["username"]
    mail = json["mail"]
    password = json["password"]

    if not username:
        return make_response(jsonify({"message": "Missing username parameter"}), 400)
    if not mail:
        return make_response(jsonify({"message": "Missing mail parameter"}), 400)
    if not password:
        return make_response(jsonify({"message": "Missing password parameter"}), 400)

    password_hash = hashlib.sha512(password.encode("UTF-8")).hexdigest()

    user = {
        "username": username,
        "mail": mail,
        "password": password_hash
    }
    mongo.db.users.insert_one(user)
    return make_response(jsonify({'message': 'User created successfully'}), 201)


@user_bp.route("/delete", methods=["DELETE"])
@jwt_required
def delete_user():
    user = get_jwt_identity()
    mongo.db.users.delete_one({"mail": user})


@user_bp.route("/login", methods=["POST"])
def login_user():
    # TODO add validation

    if not request.is_json:
        return make_response(jsonify({'message': "Missing JSON in request"}), 400)

    json = request.get_json()

    mail = json["mail"]
    password = json["password"]

    if not mail:
        return make_response(jsonify({"message": "Missing mail parameter"}), 400)
    if not password:
        return make_response(jsonify({"message": "Missing password parameter"}), 400)

    password_hash = hashlib.sha512(password.encode("UTF-8")).hexdigest()

    user = mongo.db.users.find_one({"mail": mail, "password": password_hash})

    if not user:
        return make_response(jsonify({'message': "No matching credentials found"}), 400)

    access_token = create_access_token(identity={"_id": str(user.get("_id"))}, fresh=True)
    refresh_token = create_refresh_token(identity={"_id": str(user.get("_id"))})

    return make_response(jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200)


@user_bp.route("/test", methods=["GET"])
@jwt_required
def test_user():
    user = get_jwt_identity()
    print(user)
    return make_response("test message", 200)


@user_bp.route("/refresh", methods=["POST"])
@jwt_refresh_token_required
def refresh():
    user = get_jwt_identity()
    return make_response(jsonify({"access_token": create_access_token(identity=user, fresh=False)}), 200)


@user_bp.route("/<string:_id>", methods=["GET"])
def get_username(_id):
    user = mongo.db.users.find_one({"_id": _id})

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
        return make_response(jsonify({"message": "Unauthorized"}), 401)

    json = request.get_json()

    username = json.get("username")
    mail = json.get("mail")
    password = json.get("password")

    if not username or not mail or not password:
        return make_response(jsonify({"message": "No data in JSON"}), 400)

    oid = ObjectId(_id)

    if username:
        mongo.db.users.update({'_id': oid},
                              {'$set': {'username': username}})
    if mail:
        mongo.db.users.update({'_id': oid},
                              {'$set': {'mail': mail}})
    if password:
        password_hash = hashlib.sha512(password.encode("UTF-8")).hexdigest()
        mongo.db.users.update({'_id': oid},
                              {'$set': {'password': password_hash}})
    return make_response(jsonify({"message": "Successfully updated user"}), 200)
