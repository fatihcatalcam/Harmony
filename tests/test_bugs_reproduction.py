from Harmony.models import User, Message, Like
from Harmony.extensions import db

def test_send_message_bug_reproduction(app, client):
    """
    Reproduces the bug where a user can send a message to another user
    without having a mutual match.
    """
    with app.app_context():
        user1 = User(spotify_id="bug_user1", display_name="Bug User 1")
        user2 = User(spotify_id="bug_user2", display_name="Bug User 2")
        db.session.add_all([user1, user2])
        db.session.commit()

        user1_id = user1.id
        user2_id = user2.id

    # Login as User 1
    with client.session_transaction() as session:
        session["user_id"] = user1_id

    # Try to send a message to User 2 (NO MATCH EXISTS)
    response = client.post(
        "/messages",
        json={"sender_id": user1_id, "receiver_id": user2_id, "content": "Unsolicited Message"},
    )

    # BUG: This should be 403, but it will likely be 200
    if response.status_code == 200:
        print("\n[FAIL] Bug Reproduced: Message sent successfully without a match!")
    else:
        print(f"\n[PASS] Request rejected with status {response.status_code}")

    assert response.status_code == 403, "User was able to send a message without a match!"
