// DOM Element Selections
const profilePic = document.getElementById("profile-pic");
const loginBtn = document.getElementById("login-btn");
const logoutBtn = document.getElementById("logout-btn");
const findMatchBtn = document.getElementById("find-match-btn");
const profilesContainer = document.getElementById("profiles-container");
const sendButton = document.getElementById("send-button");

// Global değişkenler (tanımlamayı unutmayın)
let currentUser = { id: 1 }; // Örnek değer; dinamik olarak doldurun
let selectedUserId = null;

// Page Load Animations
document.addEventListener("DOMContentLoaded", () => {
    // Container animasyonu
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

    // Kullanıcı öğelerinin click event'leri
    const userItems = document.querySelectorAll('.user-item');
    userItems.forEach(item => {
      item.addEventListener('click', function() {
        const userId = this.getAttribute('data-user-id');
        const userName = this.getAttribute('data-user-name');
        selectedUserId = userId; // Seçilen kullanıcı ID'sini güncelleyin
        
        // Chat başlığını güncelle
        document.getElementById('chat-user-name').textContent = userName;
        // İsteğe bağlı: Kullanıcı resmini de güncelleyebilirsiniz.
        // const userImage = this.querySelector('img').src;
        // document.getElementById('chat-user-image').src = userImage;
  
        // API çağrısı yapan loadMessages fonksiyonunu çalıştırın (varsa)
        loadMessages(userId, userName);
      });
    });
  
    // Mesaj inputu için etkinlik dinleyicisi
    const messageInput = document.getElementById("message-input");
    if (messageInput) {
        messageInput.addEventListener("input", function() {
            sendButton.disabled = this.value.trim() === "";
        });
    }
    
    // Send button click - kullanıcıdan mesajı alıp gönderiyor (API üzerinden)
    if (sendButton) {
      sendButton.addEventListener("click", async () => {
          const messageInput = document.getElementById("message-input");
          const content = messageInput?.value.trim();
          if (!content || !selectedUserId) return;
          await sendMessage(currentUser.id, selectedUserId, content);
          // Veya API yerine basit örnek kullanıyorsanız:
          // sendMessageSimple(content);
      });
    }
  
    // Eski Yönlendirme: "message-btn" tıklandığında ilgili mesaj sayfasına yönlendirme
    document.addEventListener("click", (e) => {
        const messageBtn = e.target.closest(".message-btn"); // Tıklanan öğenin en yakınındaki .message-btn'i bulur
        if (messageBtn) {
          const userId = messageBtn.dataset.userId;
          console.log("Message button clicked, userId:", userId);
          if (userId) {
            window.location.href = `/messages/${userId}`;
          } else {
            console.error("User ID is not defined in the button's dataset.");
          }
        }
      });
      
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

// Function: Load Messages for Chat Page (API çağrısı içeren versiyon)
async function loadMessages(userId, userName) {
    if (!userId || !userName) {
        console.error("Invalid userId or userName passed to loadMessages.");
        return;
    }

    // Chat UI öğelerini güncelleme
    const chatUserName = document.getElementById("chat-user-name");
    const chatUserImage = document.getElementById("chat-user-image");
    const chatMessages = document.getElementById("chat-messages");

    if (!chatUserName || !chatUserImage || !chatMessages) {
        console.error("Chat UI elements are missing.");
        return;
    }

    chatUserName.textContent = userName;
    chatUserImage.src = `https://placehold.co/50x50`;

    // Önceki mesajları temizle
    chatMessages.innerHTML = '<p class="text-gray-500 text-center mt-4">Loading messages...</p>';

    try {
        const response = await fetch(`/api/messages/${userId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const payload = await response.json();
        const messages = Array.isArray(payload) ? payload : payload?.messages || [];

        // Loading metnini temizle
        chatMessages.innerHTML = "";

        if (!messages.length) {
            chatMessages.innerHTML = '<p class="text-gray-500 text-center mt-4">No messages yet.</p>';
            return;
        }

        messages.forEach((msg) => {
            const timestamp = msg.timestamp
                ? new Date(msg.timestamp.replace(" ", "T"))
                : new Date();
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
                    <span class="text-xs text-gray-500">${timestamp.toLocaleTimeString()}</span>
                </div>`;
            chatMessages.appendChild(messageDiv);
        });
    } catch (error) {
        console.error("Error loading messages:", error);
        chatMessages.innerHTML = '<p class="text-gray-500 text-center mt-4">Failed to load messages.</p>';
    }
}

// Function: Send Message (API çağrısı içeren versiyon)
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

        // Mesaj gönderildikten sonra, mesajları yeniden yükle
        loadMessages(receiverId, document.getElementById("chat-user-name").textContent);
        document.getElementById("message-input").value = "";
    } catch (error) {
        console.error("Error sending message:", error);
    }
}

/* Alternatif örnek: Basit mesaj ekleme (API çağrısı yerine sadece DOM güncellemesi)
function sendMessageSimple(message) {
    console.log(`Sending message: ${message}`);
    const chatMessages = document.getElementById("chat-messages");
    const messageElement = document.createElement("div");
    messageElement.className = "self-end bg-blue-100 text-blue-800 rounded-lg p-2 mb-2 max-w-xs";
    messageElement.textContent = message;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
} */

    