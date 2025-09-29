from flask_socketio import emit, join_room, leave_room

from .extensions import db, socketio
from .models import Message


def get_room(sender_id, receiver_id):
    """Generate a consistent room name for two users."""
    return "_".join(sorted([str(sender_id), str(receiver_id)]))


@socketio.on("connect")
def on_connect():
    print("Bir istemci bağlandı.")


@socketio.on("disconnect")
def on_disconnect():
    print("Bir istemci bağlantısı kesildi.")


@socketio.on("join")
def on_join(data):
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    room = get_room(sender_id, receiver_id)
    join_room(room)
    print(f"Kullanıcılar {sender_id} ve {receiver_id} room: {room}'a katıldı.")


@socketio.on("leave")
def on_leave(data):
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    room = get_room(sender_id, receiver_id)
    leave_room(room)
    print(f"Kullanıcılar {sender_id} ve {receiver_id} room: {room}'dan ayrıldı.")


@socketio.on("send_message")
def handle_send_message(data):
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    content = data.get("content")
    if not sender_id or not receiver_id or not content:
        emit("error", {"error": "Invalid data"})
        return

    message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
    db.session.add(message)
    db.session.commit()

    room = get_room(sender_id, receiver_id)
    message_data = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "content": content,
        "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
    }
    emit("receive_message", message_data, room=room)
    print("Mesaj gönderildi:", message_data)
