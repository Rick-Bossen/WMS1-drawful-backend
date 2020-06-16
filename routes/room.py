import string
import random

from flask_pymongo import ObjectId
from flask import Blueprint, request, make_response, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from helpers.database import mongo

room_bp = Blueprint("room", __name__)


@room_bp.route("/create", methods=["POST"])
@jwt_required
def create_room():
    if not request.is_json:
        return make_response(jsonify({"message": "Missing JSON in request"}), 400)

    if "rounds" not in request.get_json() or not request.get_json().get("rounds"):
        return make_response(jsonify({"message": "Missing rounds in request"}), 400)

    if "max_players" not in request.get_json() or not request.get_json().get("max_players"):
        return make_response(jsonify({"message": "Missing rounds in request"}), 400)

    rounds = int(request.get_json().get("rounds"))
    max_players = int(request.get_json().get("max_players"))

    identity = get_jwt_identity()

    _id = identity["_id"]

    while True:
        r = ''.join([random.choice(string.ascii_uppercase + string.digits) for n in range(4)])
        if not mongo.db.rooms.find_one({"_id": r}):
            break

    db_user = mongo.db.users.find_one({"_id": ObjectId(_id)})
    user = {"id": _id,
            "username": str(db_user.get("username")),
            "guest": db_user.get("guest")
            }

    room = {
        "_id": r,
        "creator_id": _id,
        "users": [user],
        "rounds": rounds,
        "max_players": max_players
    }

    mongo.db.rooms.insert_one(room)
    return make_response(jsonify({"room_id": r}), 200)


@room_bp.route("/join", methods=["POST"])
@jwt_required
def join_room():
    if not request.is_json:
        return make_response(jsonify({"message": "Missing JSON in request"}), 400)

    if "join_code" not in request.get_json() or not request.get_json().get("join_code"):
        return make_response(jsonify({"message": "Missing join_code in request"}), 400)

    join_code = request.get_json().get("join_code")
    room = mongo.db.rooms.find_one({"_id": join_code})

    if not room:
        return make_response(jsonify({"message": "Room not found"}), 404)

    _id = get_jwt_identity()["_id"]
    users = room.get("users")

    if _id in list(i.get("id") for i in users):
        return make_response(jsonify({"message": "User already in room"}), 403)

    if len(users) >= room.get("max_players"):
        return make_response(jsonify({"message": "Room is full"}), 404)

    user = {"id": _id,
            "username": str(mongo.db.users.find_one({"_id": ObjectId(_id)}).get("username")),
            "guest": user.get("guest")
            }

    users.append(user)

    mongo.db.rooms.update({"_id": join_code},
                          {"$set": {"users": users}})

    return make_response(jsonify({"message": "Successfully joined room"}), 200)


@room_bp.route("/<string:join_code>", methods=["GET"])
@jwt_required
def get_room(join_code):
    room = mongo.db.rooms.find_one({"_id": join_code})

    if not room:
        return make_response(jsonify({"message": "Room not found"}), 404)

    _id = get_jwt_identity()["_id"]

    if _id not in list(i.get("id") for i in room.get("users")):
        return make_response(jsonify({"message": "User not in room"}), 403)

    return make_response(room, 200)


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
