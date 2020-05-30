from flask import Flask, make_response, jsonify
from flask_cors import CORS
from database import mongo
from jwt_global import jwt

from game import game_bp
from room import room_bp
from user import user_bp

# Create app
app = Flask(__name__)
app.config["DEBUG"] = True

# Init CORS
CORS(app)

# Init database connection
app.config['MONGO_URI'] = 'mongodb://127.0.0.1:27017/drawful'
mongo.init_app(app)

# Init jwt
# TODO generate random key
app.config['JWT_SECRET_KEY'] = 'this-is-a-random-key-2323f402vf3h49jh3vb4hrtjk34h5lw34n5vw83l4locmwe4nmtcsek4,5vuy5'
jwt.init_app(app)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'message': 'Not found'}), 404)


# Register blueprints
app.register_blueprint(game_bp, url_prefix="/game")
app.register_blueprint(room_bp, url_prefix="/room")
app.register_blueprint(user_bp, url_prefix="/user")

app.run()
