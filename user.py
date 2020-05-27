from flask import Blueprint, request, make_response, jsonify
from database import mongo
import hashlib

user_bp = Blueprint("user", __name__)


@user_bp.route("/create", methods=["POST"])
def create_user():
    # TODO add validation

    if not request.is_json:
        return make_response("Data is not json", 400)

    json = request.get_json()
    password_hash = hashlib.sha512(json["password"].encode("UTF-8")).hexdigest()
    user = {
        "username": json["username"],
        "mail": json["mail"],
        "password": password_hash
    }
    mongo.db.users.insert_one(user)
    return make_response(jsonify({'message': 'User created successfully'}), 200)
