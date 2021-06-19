import os
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

class Files:
    """Helper class for flask transcript app"""

    @classmethod
    def get_all_files(cls) -> List:
        files = os.listdir(
            os.getcwd() + "/src/transcripts")
        all_files = []
        for html in files:
            if html.endswith(".html"):
                all_files.append(html)

        return all_files

    @classmethod
    def find_file(cls, file: str) -> bool:
        all_files = cls.get_all_files()
        print(bool(file in all_files))
        return bool(file in all_files)

@app.route("/")
def index():
    return "please enter a valid ticket link to /direct?link=<link>"

@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy-policy.html")

@app.route("/cookie-policy")
def cookie_policy():
    return render_template("cookie-policy.html")

@app.route('/direct')
@limiter.limit("1/second", override_defaults=False)
def home():
    try:
        link = request.args.get('link')
        link_parts = link.split("/")
        file_name = link_parts[-1]
        print(f"input file: {file_name}")
        if Files.find_file(file_name):
            print('b')
            return render_template(file_name)
        return "invalid url"
    except Exception as e:
        print(e)
        return "invalid url"


@app.errorhandler(404)
@limiter.limit("1/second", override_defaults=False)
def not_found_error(error):
    return "404 Error", 404


if __name__ == '__main__':
    app.run(port=1337)
