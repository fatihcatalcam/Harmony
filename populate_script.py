import sys
from Harmony import create_app
from Harmony.extensions import db
from Harmony.models import User, Like
from faker import Faker
import random

def populate():
    app = create_app()
    with app.app_context():
        print("Populating database...")
        fake = Faker()
        genres_pool = ["pop", "rock", "jazz", "blues", "hip-hop", "classical", "electronic", "country"]

        users_created = 0
        for _ in range(50):
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
            users_created += 1

        db.session.commit()
        print(f"Created {users_created} users.")

        # Add likes
        users = User.query.all()
        if len(users) < 2:
            print("Not enough users to create likes.")
            return

        likes_created = 0
        for user in users:
            others = [u for u in users if u.id != user.id]
            # Like a random number of other users
            liked_users = random.sample(others, k=min(len(others), random.randint(1, len(others))))
            for liked_user in liked_users:
                if not Like.query.filter_by(from_user_id=user.id, to_user_id=liked_user.id).first():
                    db.session.add(Like(from_user_id=user.id, to_user_id=liked_user.id))
                    likes_created += 1
        
        db.session.commit()
        print(f"Created {likes_created} likes.")

if __name__ == "__main__":
    populate()
