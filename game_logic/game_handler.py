import random
from collections import Counter
from time import time

from flask_pymongo import ObjectId

from game_logic.word_parser import words
from helpers.database import mongo
import game_logic.game_thread


def start_game(match_id):
    result = mongo.db.games.update({"_id": ObjectId(match_id)},
                                   {"$set": {"status": "drawing",
                                             "theme": random_word(),
                                             "guesses": {},
                                             "votes": {},
                                             "unresponsive_users": [],
                                             "updated_at": int(time())
                                             }})

    game_logic.game_thread.BackgroundThread(match_id).start()


def submit_drawing(match_id, drawing):
    advance_game(match_id, drawing)


def submit_guess(match_id, guess, user_id):
    game = mongo.db.games.find_one({"_id": ObjectId(match_id)})
    guesses = game.get("guesses")
    active_user_count = len(game.get("users")) - len(game.get("unresponsive_users"))

    if user_id not in guesses:
        guesses[user_id] = guess

    if game.get("user_drawing") not in game.get("unresponsive_users"):
        active_user_count = active_user_count - 1

    if len(guesses) == active_user_count:
        guesses["answer"] = game.get("theme")
        advance_game(match_id, guesses)
    else:
        mongo.db.games.update({"_id": ObjectId(match_id)},
                              {'$set': {"guesses": guesses}})


def submit_vote(match_id, voted_user, user_id):
    game = mongo.db.games.find_one({"_id": ObjectId(match_id)})
    votes = game.get("votes")
    active_user_count = len(game.get("users")) - len(game.get("unresponsive_users"))

    if user_id not in votes:
        votes[user_id] = voted_user

    if game.get("user_drawing") not in game.get("unresponsive_users"):
        active_user_count = active_user_count - 1

    if len(votes) == active_user_count:
        advance_game(match_id, votes)
    else:
        mongo.db.games.update({"_id": ObjectId(match_id)},
                              {'$set': {"votes": votes}})


def random_word():
    return random.choice(words)


def user_timeout(match_id):
    game = mongo.db.games.find_one({"_id": ObjectId(match_id)})

    if game.get("status") == "drawing":
        unresponsive_users = game.get("unresponsive_users")

        if game.get("user_drawing") not in unresponsive_users:
            unresponsive_users.append(game.get("user_drawing"))

        mongo.db.games.update({"_id": ObjectId(match_id)},
                              {'$set': {"updated_at": int(time()),
                                        "guesses": {},
                                        "unresponsive_users": unresponsive_users,
                                        "status": "guessing"
                                        }})
    elif game.get("status") == "guessing":
        unresponsive_users = list(set(i.get("id") for i in game.get("users")) - set(game.get("guesses").keys()))

        if game.get("user_drawing") not in game.get("unresponsive_users"):
            unresponsive_users.remove(game.get("user_drawing"))

        mongo.db.games.update({"_id": ObjectId(match_id)},
                              {'$set': {"updated_at": int(time()),
                                        "votes": {},
                                        "unresponsive_users": unresponsive_users,
                                        "status": "voting"
                                        }})
    elif game.get("status") == "voting":
        unresponsive_users = list(set(i.get("id") for i in game.get("users")) - set(game.get("votes").keys()))

        if game.get("user_drawing") not in game.get("unresponsive_users"):
            unresponsive_users.remove(game.get("user_drawing"))

        mongo.db.games.update({"_id": ObjectId(match_id)},
                              {'$set': {"updated_at": int(time()),
                                        "users": get_updated_scores(game),
                                        "unresponsive_users": unresponsive_users,
                                        "status": "showing_scores"
                                        }})


def advance_game(match_id, data):
    game = mongo.db.games.find_one({"_id": ObjectId(match_id)})

    if game.get("status") == "drawing":
        mongo.db.games.update({"_id": ObjectId(match_id)},
                              {'$set': {"updated_at": int(time()),
                                        "drawing": data,
                                        "guesses": {},
                                        "status": "guessing"
                                        }})
    elif game.get("status") == "guessing":
        mongo.db.games.update({"_id": ObjectId(match_id)},
                              {'$set': {"updated_at": int(time()),
                                        "guesses": data,
                                        "votes": {},
                                        "status": "voting"
                                        }})
    elif game.get("status") == "voting":
        # First update votes alone because scores rely on it
        mongo.db.games.update({"_id": ObjectId(match_id)},
                              {'$set': {"votes": data}})

        mongo.db.games.update({"_id": ObjectId(match_id)},
                              {'$set': {"updated_at": int(time()),
                                        "users": get_updated_scores(game),
                                        "status": "showing_scores"
                                        }})

    elif game.get("status") == "showing_scores":
        users = list(i.get("id") for i in game.get("users"))
        current_index = users.index(game.get("user_drawing"))
        current_round = game.get("current_round")
        boolean = True
        while boolean:
            current_index = current_index + 1
            if current_index >= len(users):
                current_index = 0
                current_round = current_round + 1

            if users[current_index] not in game.get("unresponsive_users"):
                boolean = False

        if current_round > game.get("rounds"):
            mongo.db.games.update({"_id": ObjectId(match_id)},
                                  {'$set': {"updated_at": int(time()),
                                            "status": "finished"
                                            }})

        else:
            mongo.db.games.update({"_id": ObjectId(match_id)},
                                  {'$set': {"updated_at": int(time()),
                                            "user_drawing": users[current_index],
                                            "theme": random_word(),
                                            "current_round": current_round,
                                            "drawing": {},
                                            "status": "drawing"
                                            }})


def user_present(match_id, user_id):
    game = mongo.db.games.find_one({"_id": ObjectId(match_id)})
    unresponsive_users = game.get("unresponsive_users")

    if user_id in unresponsive_users:
        unresponsive_users.remove(user_id)
        mongo.db.games.update({"_id": ObjectId(match_id)},
                              {'$set': {"unresponsive_users": unresponsive_users}})


def delete_game(match_id):
    mongo.db.games.delete_one({"_id": ObjectId(match_id)})


def get_updated_scores(game):
    votes = game.get("votes")
    users = game.get("users")

    print(votes)
    counter = Counter(votes.values())
    print(counter.items())

    # Give all correct guesses 1000 points
    for user_id in (k for (k, v) in votes.items() if v == "answer"):
        for user in users:
            if user.get("id") == user_id:
                user["score"] = user["score"] + 1000

    # Give points to all voted answers
    for (k, v) in counter.items():
        if k == "answer":
            k = game.get("user_drawing")
            v = v * 2  # double points to user_drawing if correct answer is chosen

        for user in users:
            if user.get("id") == k:
                user["score"] = user["score"] + 500 * v

    return users
