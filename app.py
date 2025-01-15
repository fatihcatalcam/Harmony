from flask import Flask, request, jsonify, redirect, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from faker import Faker
import random

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
        token_response = requests.post(token_url, data=token_data)
        print("Token Response Status Code:", token_response.status_code)
        print("Token Response Content:", token_response.text)

        if token_response.status_code != 200:
            raise ValueError("Failed to fetch token")

        token_response_json = token_response.json()
        access_token = token_response_json.get("access_token")
        if not access_token:
            raise ValueError("No access token in the response")

    except Exception as e:
        return jsonify({"error": f"Error fetching access token: {str(e)}"}), 500

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        # Fetch user profile
        user_profile_url = "https://api.spotify.com/v1/me"
        user_profile_response = requests.get(user_profile_url, headers=headers)
        print("User Profile Response Status Code:", user_profile_response.status_code)
        print("User Profile Response Content:", user_profile_response.text)

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

        # Add or update the user in the database
        user = User.query.filter_by(spotify_id=spotify_id).first()
        if not user:
            user = User(
                spotify_id=spotify_id,
                display_name=display_name,
                profile_image=profile_image,
                email=email,
            )
            db.session.add(user)
            print(f"New user added: {display_name} ({spotify_id})")
        else:
            user.display_name = display_name
            user.profile_image = profile_image
            user.email = email
            print(f"Existing user updated: {display_name} ({spotify_id})")

        # Fetch top artists
        top_artists_url = "https://api.spotify.com/v1/me/top/artists"
        top_artists_response = requests.get(top_artists_url, headers=headers)
        print("Top Artists Response Status Code:", top_artists_response.status_code)
        print("Top Artists Response Content:", top_artists_response.text)

        if top_artists_response.status_code != 200:
            raise ValueError("Failed to fetch top artists")

        top_artists_data = top_artists_response.json()
        top_artists = [
            {
                "name": artist.get("name", "Unknown Artist"),
                "genres": artist.get("genres", []),
                "image": artist.get("images", [{}])[0].get("url", "/static/default_artist.png"),
                "spotify_url": artist.get("external_urls", {}).get("spotify", "#"),
            }
            for artist in top_artists_data.get("items", [])[:10]
        ]

        # Fetch top tracks
        top_tracks_url = "https://api.spotify.com/v1/me/top/tracks"
        top_tracks_response = requests.get(top_tracks_url, headers=headers)
        print("Top Tracks Response Status Code:", top_tracks_response.status_code)
        print("Top Tracks Response Content:", top_tracks_response.text)

        if top_tracks_response.status_code != 200:
            raise ValueError("Failed to fetch top tracks")

        top_tracks_data = top_tracks_response.json()
        top_tracks = [
            {
                "name": track.get("name", "Unknown Track"),
                "album": track.get("album", {}).get("name", "Unknown Album"),
                "artists": [artist.get("name", "Unknown Artist") for artist in track.get("artists", [])],
                "image": track.get("album", {}).get("images", [{}])[0].get("url", "/static/default_album.png"),
                "spotify_url": track.get("external_urls", {}).get("spotify", "#"),
            }
            for track in top_tracks_data.get("items", [])[:10]
        ]

        # Extract genres
        genres = list(set(genre for artist in top_artists for genre in artist["genres"]))

        user.top_artists = top_artists
        user.top_tracks = top_tracks
        user.genres = genres

        db.session.commit()

        # Update session
        session["user_logged_in"] = True
        session["spotify_id"] = spotify_id
        session["profile_picture_url"] = profile_image
        session["user_id"] = user.id

        return redirect(url_for("index1"))

    except Exception as e:
        print(f"Error saving user data: {str(e)}")
        return jsonify({"error": f"Error saving user data: {str(e)}"}), 500



from flask import session

@app.route("/find-profiles")
def find_profiles():
    # Oturum açmış kullanıcının ID'sini alın
    user_id = session.get("user_id")
    if not user_id:
        # Eğer oturum açılmamışsa, giriş sayfasına yönlendirin veya hata gösterin
        return redirect("/login")

    # Oturum açmış kullanıcıyı veritabanından alın
    current_user = User.query.get(user_id)
    profile_picture_url = current_user.profile_image if current_user else None

    # Tüm kullanıcı profillerini alın
    profiles = User.query.all()

    if profiles and len(profiles) > 0:
        # Gerçek veritabanı kayıtlarını kullanın
        return render_template(
            "match.html",
            profiles=profiles,
            profile_picture_url=profile_picture_url
        )
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
        return render_template(
            "match.html",
            profiles=[],
            user=fake_user,
            profile_picture_url=profile_picture_url
        )

@app.route('/api/like_profile', methods=['POST'])
def like_profile():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json()
    profile_id = data.get("profile_id")

    if not profile_id:
        return jsonify({"error": "Profile ID is required"}), 400

    # Check if the user has already liked this profile
    existing_like = Like.query.filter_by(from_user_id=current_user_id, to_user_id=profile_id).first()
    if existing_like:
        return jsonify({"message": "Profile already liked."}), 200

    # Create a new like entry
    new_like = Like(from_user_id=current_user_id, to_user_id=profile_id)
    db.session.add(new_like)
    db.session.commit()

    # Check for a mutual like
    mutual_like = Like.query.filter_by(from_user_id=profile_id, to_user_id=current_user_id).first()
    if mutual_like:
        # Return a response indicating a match
        return jsonify({"message": "It's a match!", "match": True}), 200

    return jsonify({"message": "Profile liked!", "match": False}), 200


@app.route('/api/get_likes')
def get_likes():
    likes = Like.query.all()
    data = [
        {
            "from_user": like.from_user_id,
            "to_user": like.to_user_id,
            "created_at": like.created_at
        }
        for like in likes
    ]
    return jsonify(data)

# http://127.0.0.1:5000/populate-database
@app.route("/populate-database")
def populate_database():
    fake = Faker()
    genres_pool = ["pop", "rock", "jazz", "blues", "hip-hop", "classical", "electronic", "country"]

    for _ in range(10):  # Generate 10 fake profiles
        fake_name = fake.first_name()
        fake_spotify_id = f"user_{fake.uuid4()[:8]}"
        fake_profile_image = f"https://placehold.co/80x80?text={fake_name[0]}"
        fake_top_artists = [{"name": fake.name()} for _ in range(3)]
        fake_top_tracks = [{"name": f"Track {random.randint(1, 100)}"} for _ in range(3)]
        fake_genres = random.sample(genres_pool, 2)  # Select 2 random genres

        user = User(
            spotify_id=fake_spotify_id,
            display_name=fake_name,
            profile_image=fake_profile_image,
            top_artists=fake_top_artists,
            top_tracks=fake_top_tracks,
            genres=fake_genres,
        )
        db.session.add(user)

    db.session.commit()
    return "Database populated with dynamically generated fake profiles!"

@app.route('/add-likes')
def add_likes():
    likes = [
        Like(from_user_id=10, to_user_id=1),  # Alice likes Bob
        Like(from_user_id=15, to_user_id=1),
        Like(from_user_id=18, to_user_id=1),
        Like(from_user_id=19, to_user_id=1),
        Like(from_user_id=20, to_user_id=1),
        Like(from_user_id=4, to_user_id=1),
        Like(from_user_id=5, to_user_id=32),  # Alice likes Bob
        Like(from_user_id=6, to_user_id=32),
        Like(from_user_id=7, to_user_id=32),
        Like(from_user_id=8, to_user_id=32),
    ]
    db.session.add_all(likes)
    db.session.commit()
    return "Likes added!"

@app.route('/api/matches/<int:user_id>')
def get_matches(user_id):
    matches = db.session.query(Like).filter(
        Like.from_user_id == user_id,
        Like.to_user_id.in_(
            db.session.query(Like.from_user_id).filter(Like.to_user_id == user_id)
        )
    ).all()

    data = [
        {
            "user": match.from_user_id,
            "matched_with": match.to_user_id,
            "created_at": match.created_at
        }
        for match in matches
    ]
    return jsonify(data)




@app.route("/index1")
def index1():
    user_logged_in = session.get("user_logged_in", False)
    profile_picture_url = session.get("profile_picture_url", "")
    spotify_id = session.get("spotify_id")
    user = User.query.filter_by(spotify_id=spotify_id).first()

    if not user:
        return redirect(url_for("home"))

    # Matches sorgusu
    matches = db.session.query(User).join(
        Like, (Like.to_user_id == User.id)
    ).filter(
        Like.from_user_id == user.id,
        Like.to_user_id.in_(
            db.session.query(Like.from_user_id).filter(Like.to_user_id == user.id)
        )
    ).all()

    return render_template(
        "index1.html",
        user_logged_in=user_logged_in,
        profile_picture_url=profile_picture_url,
        user=user,
        matches=matches
    )



@app.route('/api/get_profiles')
def get_profiles():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "User not logged in"}), 401

    liked_profiles = Like.query.filter_by(from_user_id=current_user_id).with_entities(Like.to_user_id).all()
    liked_profile_ids = [profile_id[0] for profile_id in liked_profiles]

    profiles = User.query.filter(
        User.id != current_user_id,
        ~User.id.in_(liked_profile_ids)
    ).all()

    if not profiles:
        print("No profiles found to display for the current user.")
        return jsonify([])

    profiles_data = [
        {
            "id": profile.id,
            "display_name": profile.display_name,
            "top_artists": [
                {"name": artist.get("name"), "image": artist.get("image", "https://placehold.co/40x40")}
                for artist in (profile.top_artists or [])[:3]
            ],
            "top_tracks": [
                {"name": track.get("name"), "image": track.get("image", "https://placehold.co/40x40")}
                for track in (profile.top_tracks or [])[:3]
            ],
            "genres": profile.genres[:5] if profile.genres else [],
            "profile_image": profile.profile_image or "https://placehold.co/80x80",
        }
        for profile in profiles
    ]

    print(f"Current user ID: {current_user_id}")
    print(f"Liked profile IDs: {liked_profile_ids}")
    print(f"Profiles fetched for display: {[p.display_name for p in profiles]}")

    return jsonify(profiles_data)




if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
