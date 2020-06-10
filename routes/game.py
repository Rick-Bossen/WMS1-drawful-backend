from flask import Blueprint, make_response, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from flask_pymongo import ObjectId

from game_logic import game_handler
from helpers.database import mongo

from time import sleep

game_bp = Blueprint("game", __name__)


@game_bp.route("/start", methods=["POST"])
@jwt_required
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

    if len(room.get("users")) < 3:
        return make_response(jsonify({"message": "Not enough users to start game"}), 400)

    users = []
    for user in room.get("users"):
        users.append({"id": user,
                      "username": str(mongo.db.users.find_one({"_id": ObjectId(user)}).get("username")),
                      "score": 0
                      })

    game = {
        "join_code": join_code,
        "creator_id": room.get("creator_id"),
        "users": users,
        "user_drawing": room.get("users")[0],
        "current_round": 0,
        "rounds": rounds
    }

    match_id = mongo.db.games.insert_one(game)
    mongo.db.rooms.delete_one({"_id": join_code})

    game_handler.start_game(str(match_id.inserted_id))
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
            if not identity["_id"] in list(i.get("id") for i in game.get("users")):
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


@game_bp.route("/<string:match_id>/status", methods=["POST"])
@jwt_required
def get_game_status(match_id):
    if not request.is_json:
        return make_response(jsonify({"message": "Missing JSON in request"}), 400)

    if "after" not in request.get_json() or not request.get_json().get("after"):
        return make_response(jsonify({"message": "Missing after in request"}), 400)

    after = request.get_json().get("after")

    game = mongo.db.games.find_one({"_id": ObjectId(match_id)})

    if not game:
        return make_response(jsonify({"message": "Match not found"}), 404)

    identity = get_jwt_identity()

    if not identity["_id"] in list(i.get("id") for i in game.get("users")):
        return make_response(jsonify({"message": "User not in game"}), 403)

    while not game.get("updated_at") > after:
        sleep(1)
        game = mongo.db.games.find_one({"_id": ObjectId(match_id)})

    game["_id"] = str(game["_id"])

    return make_response(game, 200)


@game_bp.route("/<string:match_id>/theme", methods=["GET"])
@jwt_required
def get_theme(match_id):
    game = mongo.db.games.find_one({"_id": ObjectId(match_id)})

    if not game:
        return make_response(jsonify({"message": "Match not found"}), 404)

    if game.get("status") != "drawing":
        return make_response(jsonify({"message": "Match status is not drawing"}), 403)

    identity = get_jwt_identity()

    if not identity["_id"] in list(i.get("id") for i in game.get("users")):
        return make_response(jsonify({"message": "User not in game"}), 403)

    if not identity["_id"] == game.get("user_drawing"):
        return make_response(jsonify({"message": "User is not drawing"}), 403)

    return make_response(jsonify({"theme": game.get("theme")}), 200)


@game_bp.route("/<string:match_id>/theme", methods=["POST"])
@jwt_required
def guess_theme(match_id):
    if not request.is_json:
        return make_response(jsonify({"message": "Missing JSON in request"}), 400)

    if "guess" not in request.get_json() or not request.get_json().get("guess"):
        return make_response(jsonify({"message": "Missing guess in request"}), 400)

    guess = request.get_json().get("guess")

    game = mongo.db.games.find_one({"_id": ObjectId(match_id)})

    if not game:
        return make_response(jsonify({"message": "Match not found"}), 404)

    if game.get("status") != "guessing":
        return make_response(jsonify({"message": "Match status is not guessing"}), 403)

    identity = get_jwt_identity()

    if not identity["_id"] in list(i.get("id") for i in game.get("users")):
        return make_response(jsonify({"message": "User not in game"}), 403)

    if identity["_id"] == game.get("user_drawing"):
        return make_response(jsonify({"message": "Drawing user is not allowed to guess"}), 403)

    if identity["_id"] in game.get("guesses"):
        return make_response(jsonify({"message": "User has already guessed"}), 403)

    game_handler.submit_guess(match_id, guess, identity["_id"])

    return make_response(jsonify({"message": "Guess received"}), 200)


@game_bp.route("/<string:match_id>/present", methods=["POST"])
@jwt_required
def user_present(match_id):
    game = mongo.db.games.find_one({"_id": ObjectId(match_id)})

    if not game:
        return make_response(jsonify({"message": "Match not found"}), 404)
    identity = get_jwt_identity()

    if not identity["_id"] in list(i.get("id") for i in game.get("users")):
        return make_response(jsonify({"message": "User not in game"}), 403)

    game_handler.user_present(match_id, identity["_id"])

    return make_response(jsonify({"message": "User present in game"}), 200)


@game_bp.route("/<string:match_id>/drawing/add", methods=["POST"])
@jwt_required
def add_drawing(match_id):
    if not request.is_json:
        return make_response(jsonify({"message": "Missing JSON in request"}), 400)

    if "drawing" not in request.get_json() or not request.get_json().get("drawing"):
        return make_response(jsonify({"message": "Missing drawing in request"}), 400)

    drawing = request.get_json().get("drawing")

    game = mongo.db.games.find_one({"_id": ObjectId(match_id)})

    if not game:
        return make_response(jsonify({"message": "Match not found"}), 404)
    identity = get_jwt_identity()

    if not identity["_id"] in list(i.get("id") for i in game.get("users")):
        return make_response(jsonify({"message": "User not in game"}), 403)

    game_handler.submit_drawing(match_id, drawing)

    return make_response(jsonify({"message": "Drawing successfully received"}), 200)


@game_bp.route("/<string:match_id>/theme/vote", methods=["POST"])
@jwt_required
def submit_vote(match_id):
    if not request.is_json:
        return make_response(jsonify({"message": "Missing JSON in request"}), 400)

    if "vote" not in request.get_json() or not request.get_json().get("vote"):
        return make_response(jsonify({"message": "Missing vote in request"}), 400)

    vote = request.get_json().get("vote")

    game = mongo.db.games.find_one({"_id": ObjectId(match_id)})

    if not game:
        return make_response(jsonify({"message": "Match not found"}), 404)
    identity = get_jwt_identity()

    if not identity["_id"] in list(i.get("id") for i in game.get("users")):
        return make_response(jsonify({"message": "User not in game"}), 403)

    if identity["_id"] == game.get("user_drawing"):
        return make_response(jsonify({"message": "Drawing user is not allowed to vote"}), 403)

    if identity["_id"] in game.get("votes"):
        return make_response(jsonify({"message": "User has already voted"}), 403)

    game_handler.submit_vote(match_id, vote, identity["_id"])

    return make_response(jsonify({"message": "Vote successfully received"}), 200)