import os
from flask import Flask


def create_app():
    app = Flask(__name__)

    # Load configuration from config.py or environment
    app.config.from_object('config.Config')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    

    from app.routes import bp as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
