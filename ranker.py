"""Album Ranker app"""

import base64
import hashlib
import os
import string
from random import SystemRandom

import requests
from dotenv import load_dotenv
from flask import Flask, make_response, redirect, render_template, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()
app = Flask(__name__)

if os.getenv("PROXY") is not None:
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )

CLIENT_ID = os.getenv("CLIENT_ID")
TIMEOUT = 5
SERVER_TOKEN = requests.post(
    "https://accounts.spotify.com/api/token",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    params={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": os.getenv("CLIENT_SECRET")
    },
    timeout=TIMEOUT
).json()["access_token"]
SERVER_HEADERS = {"Authorization": f"Bearer {SERVER_TOKEN}"}
CRYPTO_GENERATOR = SystemRandom()
POSSIBLE_CHARS = f"{string.ascii_letters}{string.digits}_.-~".encode("ascii")
N_POSSIBLE_CHARS = len(POSSIBLE_CHARS)
REDIRECT_URI = os.getenv("REDIRECT_URI")

def album_key(album):
    """Album sorting key function"""
    return -album["n_liked"]

def rank_albums(client_token):
    """Rank a user's albums by number of liked songs"""
    albums = {}
    track_url = "https://api.spotify.com/v1/me/tracks?limit=50&offset=0"
    while track_url is not None:
        track_response = requests.get(
            track_url,
            headers={"Authorization": f"Bearer {client_token}"},
            timeout=TIMEOUT
        ).json()
        for saved_track in track_response["items"]:
            track = saved_track["track"]
            album = track["album"]
            if album["album_type"] != "single":
                album_id = album["id"]
                if album_id not in albums:
                    albums[album_id] = {
                        "name": album["name"],
                        "image": album["images"][-1]["url"],
                        "n_total": album["total_tracks"],
                        "n_liked": 0
                    }
                albums[album_id]["n_liked"] += 1
        track_url = track_response["next"]
    perfect = []
    imperfect = []
    albums = albums.values()
    for album in albums:
        if album["n_liked"] == album["n_total"]:
            perfect.append(album)
        else:
            imperfect.append(album)
    return sorted(perfect, key=album_key), sorted(imperfect, key=album_key)

@app.route("/data")
def render_table():
    """Render the table"""
    code = request.cookies.get("code")
    code_verifier = request.get("code_verifier")
    client_token = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        params={
            "client_id": CLIENT_ID,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier
        },
        timeout=TIMEOUT
    ).json().get("access_token")
    if client_token is None:
        response = make_response(redirect(url_for("main")))
        response.delete_cookie("code")
        response.delete_cookie("code_verifier")
        return response
    perfect, imperfect = rank_albums(client_token)
    return render_template("table.html", perfect=perfect, imperfect=imperfect)

@app.route("/")
def main():
    """Album Ranker entry point"""
    code = request.args.get("code")
    code_verifier = request.cookies.get("code_verifier")
    if code is None and code_verifier is None:
        code_verifier = b""
        for _ in range(64):
            i = CRYPTO_GENERATOR.randrange(N_POSSIBLE_CHARS)
            code_verifier += POSSIBLE_CHARS[i:i + 1]

        digest = hashlib.sha256(code_verifier).digest()
        code_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        params = {
            "response_type": "code",
            "client_id": CLIENT_ID,
            "scope": "user-library-read",
            "code_challenge_method": "S256",
            "code_challenge": code_challenge,
            "redirect_uri": REDIRECT_URI
        }
        query = "&".join(f"{k}={v}" for (k, v) in params.items())

        response = make_response(render_template("auth.html", query=query))
        response.set_cookie("code_verifier", code_verifier.decode("ascii"))
        return response
    if code is not None:
        response = make_response(redirect(url_for("main")))
        response.set_cookie("code", code)
        return response
    return render_template("loading.html")
