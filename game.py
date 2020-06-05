from flask import Blueprint, make_response, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import mongo

game_bp = Blueprint("game", __name__)


@game_bp.route("/start", methods="POST")
@jwt_required
# TODO check min amount of users in game
def start_game():
    if not request.is_json:
        return make_response(jsonify({"message": "Missing JSON in request"}), 400)

    join_code = request.get_json.get("join_code")
    rounds = request.get_json.get("rounds")

    if not join_code:
        return make_response(jsonify({"message": "Missing join_code in request"}), 400)
    if not rounds:
        return make_response(jsonify({"message": "Missing rounds in request"}), 400)

    room = mongo.db.rooms.get_one({"_id": join_code})

    if not room:
        return make_response(jsonify({"message": "Room not found"}), 404)

    identity = get_jwt_identity()

    if not room.get("creator_id") == identity["_id"]:
        return make_response(jsonify({"message": "Unauthorized"}), 403)

    game = {
        "creator_id": room.get("creator_id"),
        "users": room.get("users"),
        "user_drawing": room.get("users")[0],
        "scores": dict((key, 0) for key in room.get("users")),
        "current_round": 0,
        "rounds": rounds
    }

    match_id = mongo.db.games.insert_one(game)
    mongo.db.rooms.delete_one({"_id": join_code})
    return make_response(jsonify({"message": "Game started", "match_id": match_id}), 200)
