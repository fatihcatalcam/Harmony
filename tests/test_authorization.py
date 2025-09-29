from harmony.extensions import socketio


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
