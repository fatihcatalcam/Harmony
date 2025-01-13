from flask import Flask, request, jsonify, redirect, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy
import requests
import os

app = Flask(__name__)

# Instance yolunu açıkça ayarla
desired_instance_path = os.path.abspath("C:/Users/Fatih/harmony-backend/instance")
os.makedirs(desired_instance_path, exist_ok=True)
app.instance_path = desired_instance_path

# Veritabanı Ayarları
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "your_secret_key"  # Flask oturumları için gerekli

db = SQLAlchemy(app)

# Kullanıcı Modeli
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    profile_image = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    top_artists = db.Column(db.JSON, nullable=True)
    top_tracks = db.Column(db.JSON, nullable=True)
    genres = db.Column(db.JSON, nullable=True)

# Beğeni (Likes) Modeli
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())


# Veritabanını oluşturmak için bir helper route
@app.route("/initdb")
def init_db():
    db.create_all()
    return "Veritabanı oluşturuldu!"

# Spotify API bilgileri
SPOTIFY_CLIENT_ID = "b2de7349f34f421287638527fd0612f1"
SPOTIFY_CLIENT_SECRET = "b9ad5851cac44363ad7917cb988211ea"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5000/callback"

@app.route("/user_card/<int:user_id>")
def user_card(user_id):
    # Veritabanından user_id ile eşleşen kullanıcıyı çek
    user = User.query.get_or_404(user_id)
    
    # Örnek: location veya bio alanı veritabanında yoksa, 
    # bunları user nesnesine elle ekleyebilirsiniz.
    # user.bio = "Music lover, concert goer..."
    # user.location = "New York, USA"

    return render_template("card.html", user=user)


@app.route("/")
def home():
    user_logged_in = session.get("user_logged_in", False)
    profile_picture_url = session.get("profile_picture_url", "")
    return render_template("index.html", user_logged_in=user_logged_in, profile_picture_url=profile_picture_url)


@app.route("/logout")
def logout():
    session.clear()  # Tüm oturum bilgilerini temizle
    return redirect(url_for("home"))  # Ana sayfaya yönlendir


# 1) Bu rota -> /find-profiles (tireli), fonksiyon -> find_profiles_page
@app.route("/find-profiles")
def find_profiles_page():
    """
    Bu rota, örnek profil (fake_user) datasını 'match.html' içinde göstermeyi amaçlıyor.
    """
    fake_user = {
        "display_name": "John Doe",
        "profile_image": None,
        "location": "New York, USA",
        "bio": "Music lover, concert goer, and vinyl collector.",
        "top_artists": [
            {"name": "Artist 1", "image": None},
            {"name": "Artist 2", "image": None},
            {"name": "Artist 3", "image": None},
            {"name": "Artist 4", "image": None},
            {"name": "Artist 5", "image": None},
        ],
        "top_tracks": [
            {"name": "Song 1", "image": None},
            {"name": "Song 2", "image": None},
            {"name": "Song 3", "image": None},
            {"name": "Song 4", "image": None},
            {"name": "Song 5", "image": None},
        ]
    }
    return render_template("match.html", user=fake_user)


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


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "spotify_id": user.spotify_id,
        "display_name": user.display_name,
        "profile_image": user.profile_image,
        "email": user.email,
        "top_artists": user.top_artists,
        "top_tracks": user.top_tracks,
        "genres": user.genres,
    })


@app.route("/matches/<int:user_id>", methods=["GET"])
def get_matches(user_id):
    try:
        user_likes = db.session.query(Like.to_user_id).filter(Like.from_user_id == user_id).subquery()
        matches = (
            db.session.query(User)
            .join(Like, Like.from_user_id == User.id)
            .filter(Like.to_user_id == user_id)
            .filter(User.id.in_(user_likes))
            .all()
        )

        matched_users = [
            {"id": match.id, "display_name": match.display_name, "profile_image": match.profile_image}
            for match in matches
        ]
        return jsonify({"matches": matched_users})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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


@app.route('/api/like_profile', methods=['POST'])
def like_profile():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "User not logged in"}), 401

    data = request.json
    profile_id = data.get("profile_id")
    if not profile_id:
        return jsonify({"error": "Profile ID is required"}), 400

    new_like = Like(from_user_id=current_user_id, to_user_id=profile_id)
    db.session.add(new_like)
    db.session.commit()

    return jsonify({"message": "Profile liked!"})


@app.route("/like", methods=["POST"])
def like_user():
    data = request.get_json()
    from_user_id = data.get("from_user_id")
    to_user_id = data.get("to_user_id")

    if not from_user_id or not to_user_id:
        return jsonify({"error": "User IDs are required"}), 400
    if from_user_id == to_user_id:
        return jsonify({"error": "You cannot like yourself"}), 400

    existing_like = Like.query.filter_by(from_user_id=from_user_id, to_user_id=to_user_id).first()
    if existing_like:
        return jsonify({"message": "You already liked this user"}), 400

    new_like = Like(from_user_id=from_user_id, to_user_id=to_user_id)
    db.session.add(new_like)
    db.session.commit()

    reverse_like = Like.query.filter_by(from_user_id=to_user_id, to_user_id=from_user_id).first()
    if reverse_like:
        return jsonify({"message": "It's a match!"})

    return jsonify({"message": "Like saved!"})


@app.route('/api/get_profiles')
def get_profiles():
    """
    Kullanıcının beğenmediği profilleri döndürür.
    """
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "User not logged in"}), 401

    # Kullanıcının daha önce beğendiği profilleri hariç tut
    liked_profiles = Like.query.filter_by(from_user_id=current_user_id).with_entities(Like.to_user_id).all()
    liked_profile_ids = [profile_id[0] for profile_id in liked_profiles]

    # Kullanıcının kendisi ve daha önce beğendiği profiller hariç
    profiles = User.query.filter(User.id != current_user_id, ~User.id.in_(liked_profile_ids)).all()

    # Gösterilecek profil kalmadıysa boş liste döndür
    if not profiles:
        return jsonify([])

    # Profilleri JSON formatında döndür
    profiles_data = [
        {
            "id": profile.id,
            "display_name": profile.display_name,
            "top_artists": [artist["name"] for artist in (profile.top_artists or [])[:3]],
            "top_tracks": [track["name"] for track in (profile.top_tracks or [])[:3]],
            "genres": profile.genres[:3] if profile.genres else []
        }
        for profile in profiles
    ]
    return jsonify(profiles_data)




@app.route("/find_match")
def find_match():
    user_logged_in = session.get("user_logged_in", False)
    profile_picture_url = session.get("profile_picture_url", "")
    current_user_id = session.get("current_user_id")  # Giriş yapan kullanıcı

    if not current_user_id:
        return redirect(url_for("home"))

    profiles = User.query.filter(User.id != current_user_id).all()

    for profile in profiles:
        profile.profile_image = None

    return render_template(
        "find_match.html",
        profiles=profiles,
        user_logged_in=user_logged_in,
        profile_picture_url=profile_picture_url,
    )


@app.route("/callback")
def callback():
    code = request.args.get("code")
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
        user_profile_url = "https://api.spotify.com/v1/me"
        user_profile_response = requests.get(user_profile_url, headers=headers).json()

        spotify_id = user_profile_response.get("id")
        display_name = user_profile_response.get("display_name")
        profile_image = user_profile_response.get("images", [{}])[0].get("url")
        email = user_profile_response.get("email")

        if not spotify_id or not display_name:
            raise ValueError("Incomplete user data from Spotify")
    except Exception as e:
        return jsonify({"error": f"Error fetching user profile: {str(e)}"}), 500

    try:
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

        # Top artists
        top_artists_url = "https://api.spotify.com/v1/me/top/artists"
        top_artists_response = requests.get(top_artists_url, headers=headers).json()
        top_artists = [
            {
                "name": artist["name"],
                "genres": artist["genres"],
                "image": artist["images"][0]["url"] if artist["images"] else None,
                "spotify_url": artist["external_urls"]["spotify"],
            }
            for artist in top_artists_response.get("items", [])[:10]
        ]

        # Top tracks
        top_tracks_url = "https://api.spotify.com/v1/me/top/tracks"
        top_tracks_response = requests.get(top_tracks_url, headers=headers).json()
        top_tracks = [
            {
                "name": track["name"],
                "album": track["album"]["name"],
                "artists": [artist["name"] for artist in track["artists"]],
                "image": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
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

        # Oturum bilgileri
        session["user_logged_in"] = True
        session["spotify_id"] = spotify_id
        session["profile_picture_url"] = profile_image

        return redirect(url_for("index1"))

    except Exception as e:
        return jsonify({"error": f"Error saving user data: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
