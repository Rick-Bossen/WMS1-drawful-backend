from flask import Blueprint, make_response, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from flask_pymongo import ObjectId
from database import mongo

from time import sleep

game_bp = Blueprint("game", __name__)


@game_bp.route("/start", methods=["POST"])
@jwt_required
# TODO check min amount of users in game
def start_game():
    if not request.is_json:
        return make_response(jsonify({"message": "Missing JSON in request"}), 400)

    join_code = request.get_json().get("join_code")
    rounds = request.get_json().get("rounds")

    if not join_code:
        return make_response(jsonify({"message": "Missing join_code in request"}), 400)
    if not rounds:
        return make_response(jsonify({"message": "Missing rounds in request"}), 400)

    room = mongo.db.rooms.find_one({"_id": join_code})

    if not room:
        return make_response(jsonify({"message": "Room not found"}), 404)

    identity = get_jwt_identity()

    if not room.get("creator_id") == identity["_id"]:
        return make_response(jsonify({"message": "Unauthorized"}), 403)

    game = {
        "join_code": join_code,
        "creator_id": room.get("creator_id"),
        "users": room.get("users"),
        "user_drawing": room.get("users")[0],
        "scores": dict((key, 0) for key in room.get("users")),
        "current_round": 0,
        "rounds": rounds
    }

    match_id = mongo.db.games.insert_one(game)
    mongo.db.rooms.delete_one({"_id": join_code})
    return make_response(jsonify({"message": "Game started", "match_id": str(match_id.inserted_id)}), 200)


@game_bp.route("/pending", methods=["POST"])
@jwt_required
def pending_game():
    if not request.is_json:
        return make_response(jsonify({"message": "Missing JSON in request"}), 400)

    join_code = request.get_json().get("join_code")

    if not join_code:
        return make_response(jsonify({"message": "Missing join_code in request"}), 400)

    room = mongo.db.rooms.find_one({"_id": join_code})

    identity = get_jwt_identity()

    if not room:
        game = mongo.db.games.find_one({"join_code": join_code})
        if not game:
            if identity["_id"] not in game.get("users"):
                return make_response(jsonify({"message": "Unauthorized"}), 403)

            return make_response(jsonify({"message": "Room not found"}), 404)
        else:
            return make_response(jsonify({"message": "Game started", "match_id": str(game['_id'])}), 200)

    if identity["_id"] not in room.get("users"):
        return make_response(jsonify({"message": "Unauthorized"}), 403)

    game = mongo.db.games.find_one({"join_code": join_code})
    while not game:
        sleep(1)
        game = mongo.db.games.find_one({"join_code": join_code})

    return make_response(jsonify({"message": "Game started", "match_id": str(game['_id'])}), 200)


@game_bp.route("/<string:match_id>/status", methods=["GET"])
@jwt_required
def get_game_status(match_id):

    game = mongo.db.games.find_one({"_id": ObjectId(match_id)})

    if not game:
        return make_response(jsonify({"message": "Match not found"}), 404)

    identity = get_jwt_identity()

    if not identity["_id"] in game.get("users"):
        return make_response(jsonify({"message": "User not in game"}), 403)

    game["_id"] = str(game["_id"])

    return make_response(game, 200)
