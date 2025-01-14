from flask import Flask, request, jsonify, redirect, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy
import requests
import os

# Flask uygulaması oluşturuluyor
app = Flask(__name__)

# Instance path ayarları
instance_path = os.path.abspath("instance")
os.makedirs(instance_path, exist_ok=True)
app.instance_path = instance_path

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "your_secret_key"

# Veritabanı
db = SQLAlchemy(app)

# Modeller
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    profile_image = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    top_artists = db.Column(db.JSON, nullable=True)
    top_tracks = db.Column(db.JSON, nullable=True)
    genres = db.Column(db.JSON, nullable=True)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

# Spotify API bilgileri
SPOTIFY_CLIENT_ID = "b2de7349f34f421287638527fd0612f1"
SPOTIFY_CLIENT_SECRET = "b9ad5851cac44363ad7917cb988211ea"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5000/callback"

# Rotalar
@app.route("/")
def home():
    user_logged_in = session.get("user_logged_in", False)
    profile_picture_url = session.get("profile_picture_url", "")
    return render_template("index.html", user_logged_in=user_logged_in, profile_picture_url=profile_picture_url)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/profile")
def profile():
    user_logged_in = session.get("user_logged_in", False)
    if not user_logged_in:
        return redirect(url_for("home"))

    spotify_id = session.get("spotify_id")
    user = User.query.filter_by(spotify_id=spotify_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    return render_template(
        "profile.html",
        user=user,
        top_artists=user.top_artists,
        top_tracks=user.top_tracks
    )

@app.route("/login")
def login():
    scope = "user-top-read"
    auth_url = (
        f"https://accounts.spotify.com/authorize"
        f"?client_id={SPOTIFY_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={SPOTIFY_REDIRECT_URI}"
        f"&scope={scope}"
    )
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")

    # Spotify'dan erişim token'ını alma
    token_url = "https://accounts.spotify.com/api/token"
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }

    try:
        token_response = requests.post(token_url, data=token_data).json()
        access_token = token_response.get("access_token")
        if not access_token:
            raise ValueError("Failed to fetch access token")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        # Kullanıcı profilini alma
        user_profile_url = "https://api.spotify.com/v1/me"
        user_profile_response = requests.get(user_profile_url, headers=headers).json()

        spotify_id = user_profile_response.get("id")
        display_name = user_profile_response.get("display_name")
        profile_image = user_profile_response.get("images", [{}])[0].get("url")
        email = user_profile_response.get("email")

        if not spotify_id or not display_name:
            raise ValueError("Incomplete user data from Spotify")

        # Kullanıcıyı veritabanına kaydet veya güncelle
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

        # Kullanıcının en iyi sanatçılarını alma
        top_artists_url = "https://api.spotify.com/v1/me/top/artists"
        top_artists_response = requests.get(top_artists_url, headers=headers).json()
        top_artists = [
            {
                "name": artist["name"],
                "genres": artist["genres"],
                "image": artist["images"][0]["url"] if artist.get("images") else "/static/default_artist.png",
                "spotify_url": artist["external_urls"]["spotify"],
            }
            for artist in top_artists_response.get("items", [])[:10]
        ]

        # Kullanıcının en iyi şarkılarını alma
        top_tracks_url = "https://api.spotify.com/v1/me/top/tracks"
        top_tracks_response = requests.get(top_tracks_url, headers=headers).json()
        top_tracks = [
            {
                "name": track["name"],
                "album": track["album"]["name"],
                "artists": [artist["name"] for artist in track["artists"]],
                "image": track["album"]["images"][0]["url"] if track["album"].get("images") else "/static/default_album.png",
                "spotify_url": track["external_urls"]["spotify"],
            }
            for track in top_tracks_response.get("items", [])[:10]
        ]

        # Türler
        genres = list(set(genre for artist in top_artists for genre in artist["genres"]))

        user.top_artists = top_artists
        user.top_tracks = top_tracks
        user.genres = genres

        db.session.commit()

        # Oturum bilgilerini güncelle
        session["user_logged_in"] = True
        session["spotify_id"] = spotify_id
        session["profile_picture_url"] = profile_image
        session["user_id"] = user.id

        return redirect(url_for("index1"))

    except Exception as e:
        return jsonify({"error": f"Error saving user data: {str(e)}"}), 500

@app.route("/find-profiles")
def find_profiles():
    profiles = User.query.all()

    if profiles and len(profiles) > 0:
        # Gerçek veritabanı kayıtları varsa onları kullan
        return render_template("match.html", profiles=profiles)
    else:
        # Veri yoksa test amaçlı “fake_user” gösterelim
        fake_user = {
            "display_name": "John Doe",
            "profile_image": None,
            "location": "New York, USA",
            "bio": "Music lover, concert goer, and vinyl collector.",
            "top_artists": [
                {"name": "Artist 1", "image": None},
                {"name": "Artist 2", "image": None},
                {"name": "Artist 3", "image": None},
            ],
            "top_tracks": [
                {"name": "Song 1", "image": None},
                {"name": "Song 2", "image": None},
                {"name": "Song 3", "image": None},
            ]
        }
        return render_template("match.html", user=fake_user)


@app.route("/add-test-user")
def add_test_user():
    test_user = User(
        spotify_id="test_id",
        display_name="Test User",
        profile_image="https://placehold.co/80x80",
        top_artists=[{"name": "Artist 1"}],
        top_tracks=[{"name": "Song 1"}],
    )
    db.session.add(test_user)
    db.session.commit()
    return "Test user added!"


@app.route("/index1")
def index1():
    user_logged_in = session.get("user_logged_in", False)
    profile_picture_url = session.get("profile_picture_url", "")
    spotify_id = session.get("spotify_id")
    user = User.query.filter_by(spotify_id=spotify_id).first()
    if not user:
        return redirect(url_for("home"))
    return render_template(
        "index1.html",
        user_logged_in=user_logged_in,
        profile_picture_url=profile_picture_url,
        user=user
    )

@app.route('/api/get_profiles')
def get_profiles():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "User not logged in"}), 401

    # Fetch users already liked
    liked_profiles = Like.query.filter_by(from_user_id=current_user_id).with_entities(Like.to_user_id).all()
    liked_profile_ids = [profile_id[0] for profile_id in liked_profiles]

    # Fetch profiles excluding the current user and already liked users
    profiles = User.query.filter(User.id != current_user_id, ~User.id.in_(liked_profile_ids)).all()

    if not profiles:
        print("No profiles found to display for the current user.")  # Debugging line
        return jsonify([])

    profiles_data = [
        {
            "id": profile.id,
            "display_name": profile.display_name,
            "top_artists": [artist["name"] for artist in (profile.top_artists or [])[:3]],
            "top_tracks": [track["name"] for track in (profile.top_tracks or [])[:3]],
            "genres": profile.genres[:3] if profile.genres else [],
            "profile_image": profile.profile_image or "https://placehold.co/80x80",
        }
        for profile in profiles
    ]
    print(f"Current user ID: {current_user_id}")
    print(f"Liked profiles: {liked_profile_ids}")
    print(f"All profiles excluding current user and liked profiles: {[p.display_name for p in profiles]}")

    return jsonify(profiles_data)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
