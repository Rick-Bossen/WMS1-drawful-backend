from flask import Flask
from game import game
from room import room
from user import user

# Create app
app = Flask(__name__)
app.config["DEBUG"] = True

# Register blueprints
app.register_blueprint(game)
app.register_blueprint(room)
app.register_blueprint(user)

app.run()
