import os
import glob
from typing import List

from flask import Flask, render_template, request
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter

app = Flask(__name__, template_folder="transcripts")

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "41 per hour"]
)

app.secret_key = os.urandom(24)
owd = os.getcwd()
class Files:
    """Helper class for flask transcript app"""

    @staticmethod
    def get_all_files() -> List:
        os.chdir('transcripts')
        transcripts = glob.glob("*.html")
        os.chdir(owd)
        return transcripts

    @staticmethod
    def find_transcript(link: str) -> bool:
        link_parts = link.split("/")
        file_name = link_parts[-1]
        file_name = file_name.removeprefix('transcript-')

        if not (file_name in Files.get_all_files()):
            raise ValueError
        return file_name

@app.route("/")
def index():
    return "please enter a valid ticket link to /direct?link=<link>"

@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy-policy.html")

@app.route("/cookie-policy")
def cookie_policy():
    return render_template("cookie-policy.html")

@app.route('/transcript')
@limiter.limit("1/second", override_defaults=False)
def transcript():
    link = request.args.get('link')
    if not link:
        return "invalid url"

    try:
        return render_template(Files.find_transcript(link))
    except ValueError:
        return "invalid url"


@app.errorhandler(404)
@limiter.limit("1/second", override_defaults=False)
def not_found_error(error):
    return "404 Error", 404


if __name__ == '__main__':
    app.run(port=1337)
