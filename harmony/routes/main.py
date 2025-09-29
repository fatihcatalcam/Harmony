import random

from faker import Faker
from flask import (
    Blueprint,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..extensions import csrf, db
from ..models import Like, Message, User


bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    user_logged_in = session.get("user_logged_in", False)
    profile_picture_url = session.get("profile_picture_url", "")
    return render_template(
        "index.html", user_logged_in=user_logged_in, profile_picture_url=profile_picture_url
    )


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.home"))


@bp.route("/profile")
def profile():
    user_logged_in = session.get("user_logged_in", False)
    if not user_logged_in:
        return redirect(url_for("main.home"))

    spotify_id = session.get("spotify_id")
    user = User.query.filter_by(spotify_id=spotify_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    return render_template(
        "profile.html",
        user=user,
        top_artists=user.top_artists,
        top_tracks=user.top_tracks,
        current_user_id=session.get("user_id"),
    )


@bp.route("/profile/<int:user_id>")
def view_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return render_template(
        "profile.html",
        user=user,
        top_artists=user.top_artists,
        top_tracks=user.top_tracks,
        genres=user.genres,
    )


@csrf.exempt
@bp.route("/update_profile", methods=["POST"])
def update_profile():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    bio = request.form.get("bio")
    age = request.form.get("age")
    location = request.form.get("location")

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.bio = bio
    try:
        user.age = int(age) if age else None
    except ValueError:
        user.age = None
    user.location = location

    db.session.commit()
    return jsonify({"message": "Profile updated successfully!"})


@bp.route("/find-profiles")
def find_profiles():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    current_user = User.query.get(user_id)
    profile_picture_url = current_user.profile_image if current_user else None

    liked_rows = Like.query.filter_by(from_user_id=user_id).with_entities(Like.to_user_id).all()
    liked_user_ids = {row[0] for row in liked_rows}

    mutual_match_ids = set()
    if liked_user_ids:
        mutual_rows = (
            Like.query.filter(Like.from_user_id.in_(list(liked_user_ids)), Like.to_user_id == user_id)
            .with_entities(Like.from_user_id)
            .all()
        )
        mutual_match_ids = {row[0] for row in mutual_rows}

    exclude_ids = {user_id} | liked_user_ids | mutual_match_ids

    profiles_query = User.query
    if exclude_ids:
        profiles_query = profiles_query.filter(User.id.notin_(list(exclude_ids)))

    profiles = profiles_query.all()

    return render_template(
        "match.html",
        profiles=profiles,
        profile_picture_url=profile_picture_url,
        no_profiles=len(profiles) == 0,
    )


@csrf.exempt
@bp.route("/api/like_profile", methods=["POST"])
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


@bp.route("/check-matches")
def check_matches():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return render_template(
            "check-matches.html",
            matches=[],
            profile_picture_url=session.get("profile_picture_url"),
        )

    likes_received = Like.query.filter_by(to_user_id=current_user_id).all()
    likes_given = Like.query.filter_by(from_user_id=current_user_id).all()

    likes_given_map = {like.to_user_id: like.created_at for like in likes_given}
    matched_users_with_time = []

    for like in likes_received:
        other_user_id = like.from_user_id
        if other_user_id in likes_given_map:
            match_time = max(like.created_at, likes_given_map[other_user_id])
            matched_users_with_time.append((other_user_id, match_time))

    if not matched_users_with_time:
        return render_template(
            "check-matches.html",
            matches=[],
            profile_picture_url=session.get("profile_picture_url"),
        )

    matched_users_with_time.sort(key=lambda item: item[1], reverse=True)
    ordered_match_ids = [user_id for user_id, _ in matched_users_with_time]

    matched_profiles = User.query.filter(User.id.in_(ordered_match_ids)).all()
    profiles_by_id = {user.id: user for user in matched_profiles}
    ordered_profiles = [profiles_by_id[user_id] for user_id in ordered_match_ids if user_id in profiles_by_id]

    matches_data = [
        {
            "id": user.id,
            "display_name": user.display_name,
            "profile_image": user.profile_image,
            "top_artists": user.top_artists,
            "top_tracks": user.top_tracks,
        }
        for user in ordered_profiles
    ]

    return render_template(
        "check-matches.html",
        matches=matches_data,
        profile_picture_url=session.get("profile_picture_url"),
    )


@bp.route("/chat")
def chat():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return redirect(url_for("auth.login"))

    likes_received = Like.query.filter_by(to_user_id=current_user_id).with_entities(Like.from_user_id).all()
    likes_given = Like.query.filter_by(from_user_id=current_user_id).with_entities(Like.to_user_id).all()
    liked_users = {like[0] for like in likes_given}
    matched_ids = [like[0] for like in likes_received if like[0] in liked_users]

    matches = User.query.filter(User.id.in_(matched_ids)).all()

    return render_template("chat.html", matches=matches, current_user_id=current_user_id)


@bp.route("/populate-database")
def populate_database():
    fake = Faker()
    genres_pool = ["pop", "rock", "jazz", "blues", "hip-hop", "classical", "electronic", "country"]

    for _ in range(10):
        fake_name = fake.first_name()
        spotify_id = f"fake_{fake.uuid4()}"
        if User.query.filter_by(spotify_id=spotify_id).first():
            continue

        top_artists = [
            {
                "name": fake.first_name(),
                "image": "https://placehold.co/80x80",
                "genres": random.sample(genres_pool, k=min(len(genres_pool), 3)),
            }
            for _ in range(3)
        ]

        top_tracks = [
            {
                "name": fake.sentence(nb_words=3),
                "image": "https://placehold.co/80x80",
                "artists": [fake.first_name() for _ in range(2)],
            }
            for _ in range(3)
        ]

        genres = random.sample(genres_pool, k=min(len(genres_pool), 5))

        user = User(
            spotify_id=spotify_id,
            display_name=fake_name,
            profile_image="https://placehold.co/80x80",
            email=fake.email(),
            top_artists=top_artists,
            top_tracks=top_tracks,
            genres=genres,
            bio=fake.text(max_nb_chars=200),
            age=random.randint(18, 50),
            location=fake.city(),
        )

        db.session.add(user)

    db.session.commit()
    return jsonify({"message": "Database populated with fake users."})


@bp.route("/add-likes")
def add_likes():
    users = User.query.all()
    if len(users) < 2:
        return jsonify({"message": "Not enough users to create likes."})

    for user in users:
        others = [u for u in users if u.id != user.id]
        liked_users = random.sample(others, k=min(len(others), random.randint(1, len(others))))
        for liked_user in liked_users:
            if not Like.query.filter_by(from_user_id=user.id, to_user_id=liked_user.id).first():
                db.session.add(Like(from_user_id=user.id, to_user_id=liked_user.id))

    db.session.commit()
    return jsonify({"message": "Likes added between users."})


@bp.route("/api/get_profiles")
def get_profiles_api():
    profiles = User.query.all()
    profiles_data = [
        {
            "id": profile.id,
            "display_name": profile.display_name,
            "top_artists": [
                {
                    "name": artist.get("name"),
                    "image": artist.get("image", "https://placehold.co/40x40"),
                }
                for artist in (profile.top_artists or [])[:3]
            ],
            "top_tracks": [
                {
                    "name": track.get("name"),
                    "image": track.get("image", "https://placehold.co/40x40"),
                }
                for track in (profile.top_tracks or [])[:3]
            ],
            "genres": profile.genres[:5] if profile.genres else [],
            "profile_image": profile.profile_image or "https://placehold.co/80x80",
        }
        for profile in profiles
    ]
    return jsonify(profiles_data)


@bp.route("/api/messages/<int:receiver_id>")
def get_messages_api(receiver_id):
    session_user_id = session.get("user_id")
    if not session_user_id:
        return jsonify({"error": "User not logged in"}), 401

    if receiver_id == session_user_id:
        return jsonify({"error": "Forbidden"}), 403

    if not check_match(session_user_id, receiver_id):
        return jsonify({"error": "Forbidden"}), 403

    user_id = session_user_id
    messages = (
        Message.query.filter(
            ((Message.sender_id == user_id) & (Message.receiver_id == receiver_id))
            | ((Message.sender_id == receiver_id) & (Message.receiver_id == user_id))
        )
        .order_by(Message.timestamp)
        .all()
    )
    return jsonify(
        [
            {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "content": msg.content,
                "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for msg in messages
        ]
    )


@bp.route("/messages/<int:user_id>")
def messages(user_id):
    current_user_id = session.get("user_id")
    if not current_user_id:
        return redirect(url_for("auth.login"))

    chat_partner = User.query.filter_by(id=user_id).first()
    if not chat_partner:
        return "User not found", 404

    current_user = User.query.get(current_user_id)

    messages = (
        Message.query.filter(
            ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id))
            | ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
        )
        .order_by(Message.timestamp)
        .all()
    )

    matches = []
    if current_user:
        matches = (
            db.session.query(User)
            .join(Like, (Like.to_user_id == User.id))
            .filter(
                Like.from_user_id == current_user.id,
                Like.to_user_id.in_(
                    db.session.query(Like.from_user_id).filter(Like.to_user_id == current_user.id)
                ),
            )
            .all()
        )

    return render_template(
        "message.html",
        messages=messages,
        user=chat_partner,
        matches=matches,
        current_user=current_user,
        current_user_id=current_user_id,
    )


@bp.route("/messages", methods=["POST"])
def send_message():
    session_user_id = session.get("user_id")

    def handle_auth_error(status_code, message):
        if request.is_json:
            return jsonify({"error": message}), status_code
        abort(status_code)

    if session_user_id is None:
        return handle_auth_error(401, "User not logged in")

    if request.is_json:
        data = request.get_json()
        sender_id = data.get("sender_id")
        receiver_id = data.get("receiver_id")
        content = data.get("content")
    else:
        sender_id = request.form.get("sender_id")
        receiver_id = request.form.get("receiver_id")
        content = request.form.get("message")

    if not sender_id or not receiver_id or not content:
        return jsonify({"error": "Invalid data"}), 400

    try:
        sender_id = int(sender_id)
        receiver_id = int(receiver_id)
        session_sender_id = int(session_user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid sender or receiver ID"}), 400

    if sender_id != session_sender_id:
        return handle_auth_error(403, "Forbidden")

    message = Message(
        sender_id=session_sender_id, receiver_id=receiver_id, content=content
    )
    db.session.add(message)
    db.session.commit()

    if not request.is_json:
        return redirect(request.referrer or url_for("main.home"))

    return jsonify({"message": "Message sent successfully"}), 200


@bp.route("/index1")
def index1():
    user_logged_in = session.get("user_logged_in", False)
    profile_picture_url = session.get("profile_picture_url", "")
    spotify_id = session.get("spotify_id")
    user = User.query.filter_by(spotify_id=spotify_id).first()
    if not user:
        return redirect(url_for("main.home"))

    matches = (
        db.session.query(User)
        .join(Like, (Like.to_user_id == User.id))
        .filter(
            Like.from_user_id == user.id,
            Like.to_user_id.in_(
                db.session.query(Like.from_user_id).filter(Like.to_user_id == user.id)
            ),
        )
        .all()
    )

    return render_template(
        "index1.html",
        user_logged_in=user_logged_in,
        profile_picture_url=profile_picture_url,
        matches=matches,
        user=user,
    )
