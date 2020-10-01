import logging.handlers
import os

from flask import Flask

from blueprints.users_blueprint import users_blueprint
from blueprints.posts_blueprint import posts_blueprint
from blueprints.requests_blueprint import requests_blueprint
from blueprints.chat_rooms_blueprint import chat_rooms_blueprint
from blueprints.alerts_blueprint import alerts_blueprint
from blueprints.error_blueprint import errors_blue_print
from pathlib import Path

app = Flask(__name__)

log_path = os.path.join(
    Path(os.path.dirname(
        os.path.abspath(__file__))), 'flask_instance.log')

app.logger.addHandler(
    logging.handlers.RotatingFileHandler(
        filename=log_path, mode='a',
        maxBytes=10485760, backupCount=5,
        encoding='utf-8', delay=False))

app.logger.setLevel(logging.DEBUG)

app.register_blueprint(users_blueprint)
app.register_blueprint(posts_blueprint)
app.register_blueprint(requests_blueprint)
app.register_blueprint(chat_rooms_blueprint)
app.register_blueprint(alerts_blueprint)
app.register_blueprint(errors_blue_print)


@app.errorhandler(404)
def not_found_error(error):
    return str(error), 404
