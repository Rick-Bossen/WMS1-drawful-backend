import string
import random

from flask import Blueprint, request, make_response, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from helpers.database import mongo

room_bp = Blueprint("room", __name__)


@room_bp.route("/create", methods=["POST"])
@jwt_required
def create_room():
    identity = get_jwt_identity()

    _id = identity["_id"]

    while True:
        r = ''.join([random.choice(string.ascii_uppercase + string.digits) for n in range(4)])
        if not mongo.db.rooms.find_one({"_id": r}):
            break

    print(r)
    room = {
        "_id": r,
        "creator_id": _id,
        "users": [_id]
    }
    mongo.db.rooms.insert_one(room)
    return make_response(jsonify({"room_id": r}), 200)


@room_bp.route("/join", methods=["POST"])
@jwt_required
def join_room():
    if not request.is_json:
        return make_response(jsonify({"message": "Missing JSON in request"}), 400)

    join_code = request.get_json().get("join_code")
    room = mongo.db.rooms.find_one({"_id": join_code})

    if not room:
        return make_response(jsonify({"message": "Room not found"}), 404)

    _id = get_jwt_identity()["_id"]
    users = room.get("users")

    if _id in users:
        return make_response(jsonify({"message": "User already in room"}), 403)

    if len(users) >= 8:
        return make_response(jsonify({"message": "Room is full"}), 404)

    users.append(_id)

    mongo.db.rooms.update({"_id": join_code},
                          {"$set": {"users": users}})

    return make_response(jsonify({"message": "Successfully joined room"}), 200)


@room_bp.route("/<string:join_code>/players", methods=["GET"])
@jwt_required
def get_players(join_code):
    room = mongo.db.rooms.find_one({"_id": join_code})

    if not room:
        return make_response(jsonify({"message": "Room not found"}), 404)

    _id = get_jwt_identity()["_id"]
    users = room.get("users")

    if _id not in users:
        return make_response(jsonify({"message": "User not in room"}), 403)

    return make_response(jsonify({"users": room.get("users")}), 200)


@room_bp.route("/<string:join_code>/leave", methods=["DELETE"])
@jwt_required
def remove_player(join_code):
    room = mongo.db.rooms.find_one({"_id": join_code})

    if not room:
        return make_response(jsonify({"message": "Room not found"}), 404)

    _id = get_jwt_identity()["_id"]
    users = room.get("users")

    if _id not in users:
        return make_response(jsonify({"message": "User not in room"}), 403)

    users.remove(_id)

    mongo.db.rooms.update({"_id": join_code},
                          {"$set": {"users": users}})

    return make_response(jsonify({"message": "Successfully left room"}), 200)
