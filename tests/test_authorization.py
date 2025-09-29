from harmony.extensions import db, socketio
from harmony.models import Like, Message, User


def test_send_message_requires_login(client):
    response = client.post(
        "/messages",
        json={"sender_id": 1, "receiver_id": 2, "content": "Hello"},
    )
    assert response.status_code == 401
    assert response.is_json
    assert response.get_json() == {"error": "User not logged in"}


def test_send_message_forbidden_with_mismatched_sender(client):
    with client.session_transaction() as session:
        session["user_id"] = 1

    response = client.post(
        "/messages",
        json={"sender_id": 2, "receiver_id": 3, "content": "Hello"},
    )
    assert response.status_code == 403
    assert response.is_json
    assert response.get_json() == {"error": "Forbidden"}


def test_send_message_form_flow_forbidden_with_mismatched_sender(client):
    with client.session_transaction() as session:
        session["user_id"] = 1

    response = client.post(
        "/messages",
        data={"sender_id": "2", "receiver_id": "3", "message": "Hi"},
    )
    assert response.status_code == 403


def test_socket_send_message_requires_login(app, client):
    socket_client = socketio.test_client(app, flask_test_client=client)
    assert socket_client.is_connected(), "Socket.IO test client failed to connect"
    # Clear any connection events before emitting test data.
    socket_client.get_received(namespace="/")
    socket_client.emit(
        "send_message",
        {"sender_id": 1, "receiver_id": 2, "content": "Hi"},
        namespace="/",
    )
    received = socket_client.get_received(namespace="/")
    if not received:
        received = socket_client.get_received(namespace="/")
    assert received, "No events were received from the Socket.IO server"
    assert any(
        event["name"] == "error" and event["args"][0]["error"] == "User not logged in"
        for event in received
    )
    socket_client.disconnect()


def test_socket_send_message_forbidden_with_mismatched_sender(app, client):
    with client.session_transaction() as session:
        session["user_id"] = 1

    socket_client = socketio.test_client(app, flask_test_client=client)
    assert socket_client.is_connected(), "Socket.IO test client failed to connect"
    socket_client.get_received(namespace="/")
    socket_client.emit(
        "send_message",
        {"sender_id": 2, "receiver_id": 3, "content": "Hi"},
        namespace="/",
    )
    received = socket_client.get_received(namespace="/")
    if not received:
        received = socket_client.get_received(namespace="/")
    assert received, "No events were received from the Socket.IO server"
    assert any(
        event["name"] == "error" and event["args"][0]["error"] == "Forbidden"
        for event in received
    )
    socket_client.disconnect()


def test_get_messages_requires_login(client):
    response = client.get("/api/messages/1")
    assert response.status_code == 401
    assert response.get_json() == {"error": "User not logged in"}


def test_get_messages_forbidden_without_mutual_like(app, client):
    with app.app_context():
        user1 = User(spotify_id="user1", display_name="User 1")
        user2 = User(spotify_id="user2", display_name="User 2")
        db.session.add_all([user1, user2])
        db.session.commit()

        user1_id = user1.id
        receiver_id = user2.id

    with client.session_transaction() as session_data:
        session_data["user_id"] = user1_id

    response = client.get(f"/api/messages/{receiver_id}")
    assert response.status_code == 403
    assert response.get_json() == {"error": "Forbidden"}


def test_get_messages_forbidden_when_requesting_self(app, client):
    with app.app_context():
        user = User(spotify_id="self_user", display_name="Self User")
        db.session.add(user)
        db.session.commit()

        user_id = user.id

    with client.session_transaction() as session_data:
        session_data["user_id"] = user_id

    response = client.get(f"/api/messages/{user_id}")
    assert response.status_code == 403
    assert response.get_json() == {"error": "Forbidden"}


def test_get_messages_success_for_mutual_match(app, client):
    with app.app_context():
        user1 = User(spotify_id="match_user1", display_name="Match User 1")
        user2 = User(spotify_id="match_user2", display_name="Match User 2")
        db.session.add_all([user1, user2])
        db.session.commit()

        user1_id = user1.id
        receiver_id = user2.id

        like1 = Like(from_user_id=user1_id, to_user_id=receiver_id)
        like2 = Like(from_user_id=receiver_id, to_user_id=user1_id)
        db.session.add_all([like1, like2])
        db.session.commit()

        message = Message(sender_id=user1_id, receiver_id=receiver_id, content="Hello")
        db.session.add(message)
        db.session.commit()

    with client.session_transaction() as session_data:
        session_data["user_id"] = user1_id

    response = client.get(f"/api/messages/{receiver_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["content"] == "Hello"
    assert data[0]["sender_id"] == user1_id
    assert data[0]["receiver_id"] == receiver_id


def test_messages_view_forbidden_without_mutual_match(app, client):
    with app.app_context():
        user1 = User(spotify_id="view_user1", display_name="View User 1")
        user2 = User(spotify_id="view_user2", display_name="View User 2")
        db.session.add_all([user1, user2])
        db.session.commit()

        user1_id = user1.id
        receiver_id = user2.id

    with client.session_transaction() as session_data:
        session_data["user_id"] = user1_id

    response = client.get(f"/messages/{receiver_id}")
    assert response.status_code == 403
    assert "You can only exchange messages with users you" in response.get_data(as_text=True)
