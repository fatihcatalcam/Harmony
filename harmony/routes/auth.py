import secrets

import requests
from flask import Blueprint, current_app, jsonify, redirect, request, session, url_for

from ..extensions import db, limiter
from ..models import User


bp = Blueprint("auth", __name__)


@bp.route("/login")
@limiter.limit("100 per day")
def login():
    scope = "user-top-read"
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state

    client_id = current_app.config["SPOTIFY_CLIENT_ID"]
    redirect_uri = current_app.config["SPOTIFY_REDIRECT_URI"]

    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&state={state}"
    )
    return redirect(auth_url)


@bp.route("/callback")
def callback():
    incoming_state = request.args.get("state")
    stored_state = session.get("oauth_state")
    if not stored_state or incoming_state != stored_state:
        session.clear()
        return jsonify({"error": "State mismatch"}), 400

    session.pop("oauth_state", None)
    code = request.args.get("code")

    client_id = current_app.config["SPOTIFY_CLIENT_ID"]
    client_secret = current_app.config["SPOTIFY_CLIENT_SECRET"]
    redirect_uri = current_app.config["SPOTIFY_REDIRECT_URI"]

    token_url = "https://accounts.spotify.com/api/token"
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    try:
        token_response = requests.post(token_url, data=token_data)
        if token_response.status_code != 200:
            raise ValueError("Failed to fetch token")
        token_response_json = token_response.json()
        access_token = token_response_json.get("access_token")
        if not access_token:
            raise ValueError("No access token in the response")
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Error fetching access token: {str(exc)}"}), 500

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        user_profile_url = "https://api.spotify.com/v1/me"
        user_profile_response = requests.get(user_profile_url, headers=headers)
        if user_profile_response.status_code != 200:
            raise ValueError("Failed to fetch user profile")
        user_profile = user_profile_response.json()

        spotify_id = user_profile.get("id")
        display_name = user_profile.get("display_name")
        profile_image = (
            user_profile.get("images")[0].get("url")
            if user_profile.get("images")
            else "https://placehold.co/80x80"
        )
        email = user_profile.get("email")
        if not spotify_id or not display_name:
            raise ValueError("Incomplete user data from Spotify")

        user = User.query.filter_by(spotify_id=spotify_id).first()
        if not user:
            user = User(
                spotify_id=spotify_id,
                display_name=display_name,
                profile_image=profile_image,
                email=email,
            )
            db.session.add(user)
        else:
            user.display_name = display_name
            user.profile_image = profile_image
            user.email = email

        top_artists_url = "https://api.spotify.com/v1/me/top/artists"
        top_artists_response = requests.get(top_artists_url, headers=headers)
        if top_artists_response.status_code == 200:
            top_artists_data = top_artists_response.json().get("items", [])
            user.top_artists = [
                {
                    "name": artist["name"],
                    "image": artist["images"][0]["url"] if artist.get("images") else None,
                    "genres": artist.get("genres", []),
                }
                for artist in top_artists_data
            ]
        else:
            user.top_artists = []

        top_tracks_url = "https://api.spotify.com/v1/me/top/tracks"
        top_tracks_response = requests.get(top_tracks_url, headers=headers)
        if top_tracks_response.status_code == 200:
            top_tracks_data = top_tracks_response.json().get("items", [])
            user.top_tracks = [
                {
                    "name": track["name"],
                    "image": track["album"]["images"][0]["url"] if track["album"].get("images") else None,
                    "artists": [artist["name"] for artist in track.get("artists", [])],
                }
                for track in top_tracks_data
            ]
        else:
            user.top_tracks = []

        combined_genres = set()
        for artist in user.top_artists or []:
            for genre in artist.get("genres", []):
                combined_genres.add(genre)
        user.genres = list(combined_genres)

        db.session.commit()

        session["user_logged_in"] = True
        session["spotify_id"] = spotify_id
        session["profile_picture_url"] = profile_image
        session["user_id"] = user.id

        return redirect(url_for("main.index1"))

    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Error saving user data: {str(exc)}"}), 500
