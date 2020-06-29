import sys
import threading

from flask_pymongo import ObjectId

from time import time
from helpers.database import mongo
import game_logic.game_handler


class BackgroundThread(threading.Thread):
    def __init__(self, match_id):
        threading.Thread.__init__(self)
        self.stopped = threading.Event()
        self.match_id = match_id

    def run(self):
        while not self.stopped.wait(1):
            game = mongo.db.games.find_one({"_id": ObjectId(self.match_id)})
            if int(time()) - game.get("updated_at") >= 60:
                game_logic.game_handler.user_timeout(self.match_id)

            elif game.get("status") == "showing_scores" and int(time()) - game.get("updated_at") >= 10:
                game_logic.game_handler.advance_from_showing_scores(self.match_id)

            elif set(i.get("id") for i in game.get("users")) == set(game.get("unresponsive_users")):
                game_logic.game_handler.delete_game(self.match_id)
                sys.exit()

