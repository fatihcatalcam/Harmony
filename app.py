from flask import Flask, request, jsonify, redirect, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from faker import Faker
import random
from flask_migrate import Migrate
from datetime import datetime
from flask_socketio import SocketIO, join_room, leave_room, emit

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
migrate = Migrate(app, db)

# SocketIO nesnesini eventlet asenkron moduyla başlatın
socketio = SocketIO(app, async_mode="eventlet")

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

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

# Spotify API bilgileri (kendi bilgilerinizi girin)
SPOTIFY_CLIENT_ID = "b2de7349f34f421287638527fd0612f1"
SPOTIFY_CLIENT_SECRET = "b9ad5851cac44363ad7917cb988211ea"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5000/callback"

# -------------------------------------------------
# WebSocket (SocketIO) Olayları
# -------------------------------------------------
def get_room(sender_id, receiver_id):
    """İki kullanıcı için ortak room adını oluşturur."""
    return '_'.join(sorted([str(sender_id), str(receiver_id)]))

@socketio.on('connect')
def on_connect():
    print("Bir istemci bağlandı.")

@socketio.on('disconnect')
def on_disconnect():
    print("Bir istemci bağlantısı kesildi.")

@socketio.on('join')
def on_join(data):
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    room = get_room(sender_id, receiver_id)
    join_room(room)
    print(f"Kullanıcılar {sender_id} ve {receiver_id} room: {room}'a katıldı.")

@socketio.on('send_message')
def handle_send_message(data):
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    if not sender_id or not receiver_id or not content:
        emit('error', {'error': 'Invalid data'})
        return
    # Mesajı veritabanına kaydet
    message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
    db.session.add(message)
    db.session.commit()

    room = get_room(sender_id, receiver_id)
    message_data = {
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'content': content,
        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    }
    emit('receive_message', message_data, room=room)
    print("Mesaj gönderildi:", message_data)

# -------------------------------------------------
# Rotalar
# -------------------------------------------------
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
    return render_template("profile.html",
                           user=user,
                           top_artists=user.top_artists,
                           top_tracks=user.top_tracks)

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

        # Örnek: Top artists, tracks ve genre hesaplamaları yapılabilir
        db.session.commit()

        session["user_logged_in"] = True
        session["spotify_id"] = spotify_id
        session["profile_picture_url"] = profile_image
        session["user_id"] = user.id

        return redirect(url_for("index1"))

    except Exception as e:
        return jsonify({"error": f"Error saving user data: {str(e)}"}), 500

@app.route("/profile/<int:user_id>")
def view_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return render_template("profile.html",
                           user=user,
                           top_artists=user.top_artists,
                           top_tracks=user.top_tracks,
                           genres=user.genres)

@app.route("/find-profiles")
def find_profiles():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    current_user = User.query.get(user_id)
    profile_picture_url = current_user.profile_image if current_user else None
    profiles = User.query.all()
    if profiles and len(profiles) > 0:
        return render_template("match.html",
                               profiles=profiles,
                               profile_picture_url=profile_picture_url)
    else:
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
        return render_template("match.html",
                               profiles=[],
                               user=fake_user,
                               profile_picture_url=profile_picture_url)

@app.route('/api/like_profile', methods=['POST'])
def like_profile():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json()
    profile_id = data.get("profile_id")
    if not profile_id:
        return jsonify({"error": "Profile ID is required"}), 400

    existing_like = Like.query.filter_by(from_user_id=current_user_id, to_user_id=profile_id).first()
    if existing_like:
        return jsonify({"message": "Profile already liked."}), 200

    new_like = Like(from_user_id=current_user_id, to_user_id=profile_id)
    db.session.add(new_like)
    db.session.commit()

    if check_match(current_user_id, profile_id):
        return jsonify({"message": "It's a match!"}), 200

    return jsonify({"message": "Profile liked!"}), 200

def check_match(user_id, other_user_id):
    like_from_user = Like.query.filter_by(from_user_id=user_id, to_user_id=other_user_id).first()
    like_from_other = Like.query.filter_by(from_user_id=other_user_id, to_user_id=user_id).first()
    return like_from_user is not None and like_from_other is not None

@app.route("/populate-database")
def populate_database():
    fake = Faker()
    genres_pool = ["pop", "rock", "jazz", "blues", "hip-hop", "classical", "electronic", "country"]

    for _ in range(10):
        fake_name = fake.first_name()
        fake_spotify_id = f"user_{fake.uuid4()[:8]}"
        fake_profile_image = f"https://placehold.co/80x80?text={fake_name[0]}"
        fake_top_artists = [{"name": fake.name()} for _ in range(3)]
        fake_top_tracks = [{"name": f"Track {random.randint(1, 100)}"} for _ in range(3)]
        fake_genres = random.sample(genres_pool, 2)
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
        Like(from_user_id=10, to_user_id=1),
        Like(from_user_id=15, to_user_id=1),
        Like(from_user_id=18, to_user_id=1),
        Like(from_user_id=19, to_user_id=1),
        Like(from_user_id=20, to_user_id=1),
        Like(from_user_id=4, to_user_id=1),
        Like(from_user_id=5, to_user_id=32),
        Like(from_user_id=6, to_user_id=32),
        Like(from_user_id=7, to_user_id=32),
        Like(from_user_id=8, to_user_id=32),
    ]
    db.session.add_all(likes)
    db.session.commit()
    return "Likes added!"

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
    return jsonify(profiles_data)

# API: Mesajları JSON olarak döndür
@app.route('/api/messages/<int:receiver_id>')
def get_messages_api(receiver_id):
    user_id = session.get('user_id')
    messages = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == receiver_id)) |
        ((Message.sender_id == receiver_id) & (Message.receiver_id == user_id))
    ).order_by(Message.timestamp).all()
    return jsonify([{
        "id": msg.id,
        "sender_id": msg.sender_id,
        "receiver_id": msg.receiver_id,
        "content": msg.content,
        "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for msg in messages])

# Sohbet sayfası: HTML şablon render et
@app.route('/messages/<int:user_id>')
def messages(user_id):
    current_user_id = session.get("user_id")
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return "User not found", 404
    messages = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
    ).order_by(Message.timestamp).all()
    return render_template("message.html", messages=messages, user=user)

# Mesaj gönderme (POST)
@app.route('/messages', methods=['POST'])
def send_message():
    # JSON verisi gönderilmişse
    if request.is_json:
        data = request.get_json()
        sender_id = data.get('sender_id')
        receiver_id = data.get('receiver_id')
        content = data.get('content')
    else:
        # Form gönderimi (application/x-www-form-urlencoded) durumu
        sender_id = request.form.get('sender_id')
        receiver_id = request.form.get('receiver_id')
        content = request.form.get('message')  # Formdaki input name="message"

    if not sender_id or not receiver_id or not content:
        return jsonify({"error": "Invalid data"}), 400

    try:
        sender_id = int(sender_id)
        receiver_id = int(receiver_id)
    except ValueError:
        return jsonify({"error": "Invalid sender or receiver ID"}), 400

    message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
    db.session.add(message)
    db.session.commit()
    
    if not request.is_json:
        return redirect(request.referrer or url_for('home'))
    
    return jsonify({"message": "Message sent successfully"}), 200

@app.route("/index1")
def index1():
    user_logged_in = session.get("user_logged_in", False)
    profile_picture_url = session.get("profile_picture_url", "")
    spotify_id = session.get("spotify_id")
    user = User.query.filter_by(spotify_id=spotify_id).first()
    if not user:
        return redirect(url_for("home"))

    matches = db.session.query(User).join(
        Like, (Like.to_user_id == User.id)
    ).filter(
        Like.from_user_id == user.id,
        Like.to_user_id.in_(
            db.session.query(Like.from_user_id).filter(Like.to_user_id == user.id)
        )
    ).all()

    return render_template("index1.html",
                           user_logged_in=user_logged_in,
                           profile_picture_url=profile_picture_url,
                           matches=matches,
                           user=user)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
