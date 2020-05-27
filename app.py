from flask import Flask, make_response, jsonify

from database import mongo

from game import game_bp
from room import room_bp
from user import user_bp

# Create app
app = Flask(__name__)
app.config["DEBUG"] = True

# Init database connection
app.config['MONGO_URI'] = 'mongodb://127.0.0.1:27017/drawful'
mongo.init_app(app)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'message': 'Not found'}), 404)


# Register blueprints
app.register_blueprint(game_bp, url_prefix="/game")
app.register_blueprint(room_bp, url_prefix="/room")
app.register_blueprint(user_bp, url_prefix="/user")

app.run()
