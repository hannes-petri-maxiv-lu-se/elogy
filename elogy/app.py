"""
The main entrypoint of the Elogy web application
"""

from time import time

from flask import Flask, current_app, send_from_directory, g
from flask_restful import Api
import logging
from peewee import OperationalError

from .db import setup_database

from .api.errors import errors as api_errors
from .api.logbooks import LogbooksResource, LogbookRevisionsResource
from .api.entries import EntryResource, EntriesResource, EntryLockResource, EntryRevisionsResource
from .api.users import UsersResource
from .api.attachments import AttachmentsResource

# Configure the main application object
app = Flask(__name__,
            static_folder="frontend/build/static",
            static_url_path="/static")
app.config.from_envvar('ELOGY_CONFIG_FILE')


# add some hooks for debugging purposes
@app.before_request
def before_request():
    g.start = time()


@app.teardown_request
def teardown_request(exception=None):
    duration = time() - g.start
    current_app.logger.debug("Request took %f s", duration)


# Database setup
#db.init_app(app)
setup_database(app.config["DATABASE"]["name"])


# Allow CORS requests. Maybe we should only enable this in debug mode?
@app.after_request
def per_request_callbacks(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


# API endpoints

api = Api(app, prefix="/api", errors=api_errors)

api.add_resource(LogbooksResource,
                 "/logbooks/",
                 "/logbooks/<int:logbook_id>/",
                 "/logbooks/<int:logbook_id>/revisions/<int:revision_n>/")

api.add_resource(LogbookRevisionsResource,
                 "/logbooks/<int:logbook_id>/revisions/")

api.add_resource(EntriesResource,
                 "/logbooks/<int:logbook_id>/entries/")  # GET

api.add_resource(EntryResource,
                 "/entries/<int:entry_id>/",
                 "/logbooks/<int:logbook_id>/entries/",   # POST, PUT
                 "/logbooks/<int:logbook_id>/entries/<int:entry_id>/",
                 "/logbooks/<int:logbook_id>/entries/<int:entry_id>/revisions/<int:revision_n>")

api.add_resource(EntryRevisionsResource,
                 "/logbooks/<int:logbook_id>/entries/<int:entry_id>/revisions/")

api.add_resource(EntryLockResource,
                 "/logbooks/<int:logbook_id>/entries/<int:entry_id>/lock",
                 "/entries/<int:entry_id>/lock")

api.add_resource(UsersResource,
                 "/users/")

api.add_resource(AttachmentsResource,
                 "/attachments/")


# other routes
@app.route('/attachments/<path:path>')
def get_attachment(path):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], path)


@app.route("/")
@app.route("/<path:path>")
def get_index(path=None):
    """
    This is a 'catch-all' that will catch anything not matched by a
    previous route, always delvering the main index file. This is
    mainly to allow client side routing to use the URL however it
    likes...
    """
    return send_from_directory("frontend/build", "index.html")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, #debug=True,
            extra_files=["templates"])  # this makes sure templates are watched
