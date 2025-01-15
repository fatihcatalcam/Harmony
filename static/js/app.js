// DOM Element Selections
const profilePic = document.getElementById("profile-pic");
const loginBtn = document.getElementById("login-btn");
const logoutBtn = document.getElementById("logout-btn");
const findMatchBtn = document.getElementById("find-match-btn");
const profilesContainer = document.getElementById("profiles-container");

// Page Load Animations
document.addEventListener("DOMContentLoaded", () => {
    const container = document.querySelector(".container");
    if (container) {
        container.style.opacity = 0;
        container.style.transform = "translateY(20px)";
        setTimeout(() => {
            container.style.transition = "opacity 0.8s ease, transform 0.8s ease";
            container.style.opacity = 1;
            container.style.transform = "translateY(0)";
        }, 200);
    }
});

// Redirect to Chat on "Message" Button Click
document.addEventListener("click", (e) => {
    if (e.target.classList.contains("message-btn")) {
        const userId = e.target.dataset.userId; // Ensure `data-user-id` exists
        if (userId) {
            window.location.href = `/messages/${userId}`;
        } else {
            console.error("User ID is not defined in the button's dataset.");
        }
    }
});


// Profile Picture Click Navigation
if (profilePic) {
    profilePic.addEventListener("click", () => {
        profilePic.style.transition = "transform 0.2s ease";
        profilePic.style.transform = "scale(0.9)";
        setTimeout(() => {
            profilePic.style.transform = "scale(1)";
            window.location.href = "/profile";
        }, 150);
    });
}

// Logout Button Functionality
if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
        e.preventDefault();
        logoutBtn.innerText = "Logging out...";
        logoutBtn.style.backgroundColor = "#f44336";
        logoutBtn.style.transition = "background-color 0.3s ease, transform 0.3s ease";
        logoutBtn.style.transform = "scale(0.95)";
        setTimeout(() => {
            window.location.href = "/logout";
        }, 500);
    });
}

// Load Messages for Chat Page
async function loadMessages(userId, userName) {
    if (!userId || !userName) {
        console.error("Invalid userId or userName passed to loadMessages.");
        return;
    }

    // Update Chat Header
    const chatUserName = document.getElementById("chat-user-name");
    const chatUserImage = document.getElementById("chat-user-image");
    const chatMessages = document.getElementById("chat-messages");

    if (!chatUserName || !chatUserImage || !chatMessages) {
        console.error("Chat UI elements are missing.");
        return;
    }

    chatUserName.textContent = userName;
    chatUserImage.src = `https://placehold.co/50x50`;

    // Clear Previous Messages
    chatMessages.innerHTML = '<p class="text-gray-500 text-center mt-4">Loading messages...</p>';

    try {
        const response = await fetch(`/messages/${userId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();

        // Clear loading text
        chatMessages.innerHTML = "";

        data.forEach((msg) => {
            const messageDiv = document.createElement("div");
            messageDiv.className = `flex w-full mt-2 space-x-3 max-w-xs ${
                msg.sender_id === currentUser.id ? "ml-auto justify-end" : ""
            }`;

            messageDiv.innerHTML = `
                <div>
                    <div class="${
                        msg.sender_id === currentUser.id
                            ? "bg-blue-600 text-white"
                            : "bg-gray-300"
                    } p-3 rounded-lg">
                        <p class="text-sm">${msg.content}</p>
                    </div>
                    <span class="text-xs text-gray-500">${new Date(msg.timestamp).toLocaleTimeString()}</span>
                </div>`;
            chatMessages.appendChild(messageDiv);
        });
    } catch (error) {
        console.error("Error loading messages:", error);
        chatMessages.innerHTML = '<p class="text-gray-500 text-center mt-4">Failed to load messages.</p>';
    }
}

// Send Message
async function sendMessage(senderId, receiverId, content) {
    if (!content || !receiverId) {
        console.error("Invalid senderId, receiverId, or content.");
        return;
    }

    try {
        const response = await fetch("/messages", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                sender_id: senderId,
                receiver_id: receiverId,
                content,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        loadMessages(receiverId, document.getElementById("chat-user-name").textContent);
        document.getElementById("message-input").value = "";
    } catch (error) {
        console.error("Error sending message:", error);
    }
}

// Attach Send Button Event Listener
const sendButton = document.getElementById("send-button");
if (sendButton) {
    console.log("Send button found");
    sendButton.addEventListener("click", () => {
        const messageInput = document.getElementById("message-input");
        const content = messageInput?.value.trim();
        if (!content || !selectedUserId) return;
        sendMessage(currentUser.id, selectedUserId, content);
    });
} else {
    console.error("Send button element is missing.");
}
