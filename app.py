from flask import Flask, make_response, jsonify
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

from dotenv import load_dotenv
import os

from helpers.database import mongo
from helpers.jwt_global import jwt

from routes import game_bp
from routes import room_bp
from routes import user_bp

# Load config
load_dotenv()

# Create app
app = Flask(__name__)
app.config["DEBUG"] = os.environ.get("DEBUG", True)

# Init CORS
CORS(app)

# Init Swagger UI
swaggerui_blueprint = get_swaggerui_blueprint(
    "/docs",
    "/static/openapi.yml"
)
app.register_blueprint(swaggerui_blueprint, url_prefix="/docs")

# Init database connection
app.config['MONGO_URI'] = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/drawful")
mongo.init_app(app)

# Init jwt
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET", "this-is-a-random-key-2323f402vf3h49jh3vb4hrtjk34h5lw34n5vw83l4locmwe4nmtcsek4,5vuy5")
jwt.init_app(app)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'message': 'Not found'}), 404)


# Register blueprints
app.register_blueprint(game_bp, url_prefix="/game")
app.register_blueprint(room_bp, url_prefix="/room")
app.register_blueprint(user_bp, url_prefix="/user")

if __name__ == "__main__":
    app.run()
