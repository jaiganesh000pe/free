from flask import Flask
from .config import Config

def create_app():
    app = Flask(__name__, template_folder="../templates")
    app.config.from_object(Config)
    from .routes import bp
    app.register_blueprint(bp)
    return app
