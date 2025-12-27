/***********************************************************
 * find_match_interact.js - Interact.js ile Tinder-Style Swipe & Animasyonlar
 ***********************************************************/

document.addEventListener("DOMContentLoaded", function () {
  const container = document.querySelector(".tinder-container");
  const cards = Array.from(document.querySelectorAll(".card"));

  if (!cards || cards.length === 0) {
    if (container) {
      container.innerHTML = `<div class="flex flex-col items-center justify-center h-full text-center p-8"><h2 class="text-2xl font-bold text-white mb-2">No Matches Found</h2><p class="text-gray-400">Check back later!</p></div>`;
    }
  }

  // Her kart için başlangıç kümülatif dx ve dy değerlerini sıfırlıyoruz.
  cards.forEach(card => {
    card.currentDx = 0;
    card.currentDy = 0;
    card.style.touchAction = "none";
  });

  // Interact.js ile kartları draggable yapıyoruz.
  interact('.card').draggable({
    inertia: true,
    listeners: {
      move: dragMoveListener,
      end: dragEndListener
    }
  });

  function dragMoveListener(event) {
    const target = event.target;
    target.currentDx = (target.currentDx || 0) + event.dx;
    target.currentDy = (target.currentDy || 0) + event.dy;
    target.style.transform = `translate(${target.currentDx}px, ${target.currentDy}px)`;
  }

  async function dragEndListener(event) {
    const target = event.target;
    const style = window.getComputedStyle(target);
    const matrix = new DOMMatrixReadOnly(style.transform);
    const cumulativeX = matrix.m41;

    if (cumulativeX > 50) {
      await handleLike(target);
    } else if (cumulativeX < -50) {
      handlePass(target);
    } else {
      target.style.transition = "transform 0.3s";
      target.style.transform = "translate(0px, 0px)";
      setTimeout(() => {
        target.currentDx = 0;
        target.currentDy = 0;
      }, 350);
    }
  }

  async function handleLike(card) {
    card.style.transition = "transform 0.5s";
    card.style.transform = "translate(400px, 0px) rotate(30deg)";
    const profileId = card.getAttribute("data-id");

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    try {
      const res = await fetch("/api/like_profile", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ profile_id: profileId })
      });

      if (!res.ok) throw new Error(`Failed to like profile: ${res.statusText}`);
      const result = await res.json();

      if (result.message === "It's a match!") {
        showMatchText();
      } else {
        showHeart();
      }
    } catch (error) {
      console.error("Error liking profile:", error);
      alert("An error occurred. Please try again.");
    }

    setTimeout(() => {
      card.remove();
      checkEmptyStack();
    }, 500);
  }

  function handlePass(card) {
    card.style.transition = "transform 0.5s";
    card.style.transform = "translate(-400px, 0px) rotate(-30deg)";
    showCross();
    setTimeout(() => {
      card.remove();
      checkEmptyStack();
    }, 500);
  }

  function checkEmptyStack() {
    const container = document.querySelector(".tinder-container");
    const remaining = container.querySelectorAll(".card");
    if (remaining.length === 0) {
      container.innerHTML = `<div class="flex flex-col items-center justify-center h-full text-center p-8"><h2 class="text-2xl font-bold text-white mb-2">No Matches Found</h2><p class="text-gray-400">Check back later!</p></div>`;
    }
  }

  // Opsiyonel: Kart üzerindeki like/pass butonlarına click event ekleyelim.
  cards.forEach(card => {
    const passBtn = card.querySelector(".pass");
    const likeBtn = card.querySelector(".like");

    if (passBtn) {
      passBtn.addEventListener("click", () => {
        handlePass(card);
      });
    }
    if (likeBtn) {
      likeBtn.addEventListener("click", async () => {
        await handleLike(card);
      });
    }
    const superLikeBtn = card.querySelector(".super-like");
    if (superLikeBtn) {
      superLikeBtn.addEventListener("click", async () => {
        await handleSuperLike(card);
      });
    }
  });

  async function handleSuperLike(card) {
    card.style.transition = "transform 0.5s";
    card.style.transform = "translate(0px, -600px) scale(0.5)"; // Fly up
    const profileId = card.getAttribute("data-id");
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    try {
      // Send super_like: true flag
      const res = await fetch("/api/like_profile", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ profile_id: profileId, super_like: true })
      });

      if (!res.ok) throw new Error(`Failed to like profile`);
      const result = await res.json();

      if (result.message === "It's a match!") {
        showMatchText();
      } else {
        showStar(); // Show star animation
      }

    } catch (err) {
      console.error(err);
    }

    setTimeout(() => {
      card.remove();
      checkEmptyStack();
    }, 500);
  }

  // Socket.IO Initialization for Real-Time Match Alerts
  const socket = io();

  socket.on("connect", () => {
    console.log("Connected to notification socket");
  });

  socket.on("match_found", (data) => {
    console.log("Real-time match notification received:", data);
    showMatchPopup(data.match_name);
  });

});

/***********************************************************
 * Animasyon Fonksiyonları
 ***********************************************************/

function showHeart() {
  const heart = document.createElement("div");
  heart.className = "heart-animation";
  heart.innerHTML = "<i class='fas fa-heart' style='font-size: 80px; color: rgba(255,255,255,0.8);'></i>";
  heart.style.position = "fixed";
  heart.style.top = "50%";
  heart.style.left = "50%";
  heart.style.transform = "translate(-50%, -50%)";
  heart.style.zIndex = "2000";
  heart.style.opacity = "0";
  heart.style.transition = "opacity 0.5s ease, transform 0.5s ease";
  document.body.appendChild(heart);
  setTimeout(() => {
    heart.style.opacity = "1";
    heart.style.transform = "translate(-50%, -50%) scale(1.2)";
  }, 50);
  setTimeout(() => { heart.remove(); }, 1000);
}

function showMatchText() {
  const matchText = document.createElement("div");
  matchText.className = "match-animation";
  matchText.innerText = "MATCH";
  matchText.style.position = "fixed";
  matchText.style.top = "50%";
  matchText.style.left = "50%";
  matchText.style.transform = "translate(-50%, -50%)";
  matchText.style.fontSize = "80px";
  matchText.style.color = "rgba(255,255,255,0.9)";
  matchText.style.zIndex = "2000";
  matchText.style.opacity = "0";
  matchText.style.transition = "opacity 0.5s ease, transform 0.5s ease";
  document.body.appendChild(matchText);
  setTimeout(() => {
    matchText.style.opacity = "1";
    matchText.style.transform = "translate(-50%, -50%) scale(1.2)";
  }, 50);
  setTimeout(() => { matchText.remove(); }, 1000);
}

function showCross() {
  const cross = document.createElement("div");
  cross.className = "cross-animation";
  cross.innerHTML = "<i class='fas fa-times' style='font-size: 80px; color: rgba(255,255,255,0.9);'></i>";
  cross.style.position = "fixed";
  cross.style.top = "50%";
  cross.style.left = "50%";
  cross.style.transform = "translate(-50%, -50%)";
  cross.style.zIndex = "2000";
  cross.style.opacity = "0";
  cross.style.transition = "opacity 0.5s ease, transform 0.5s ease";
  document.body.appendChild(cross);
  setTimeout(() => {
    cross.style.opacity = "1";
    cross.style.transform = "translate(-50%, -50%) scale(1.2)";
  }, 50);
  setTimeout(() => { cross.remove(); }, 1000);
}

function showStar() {
  const star = document.createElement("div");
  star.className = "star-animation";
  star.innerHTML = "<i class='fas fa-star' style='font-size: 80px; color: #3b82f6;'></i>";
  star.style.position = "fixed";
  star.style.top = "50%";
  star.style.left = "50%";
  star.style.transform = "translate(-50%, -50%)";
  star.style.zIndex = "2000";
  star.style.opacity = "0";
  star.style.transition = "opacity 0.5s ease, transform 0.5s ease";
  document.body.appendChild(star);
  setTimeout(() => {
    star.style.opacity = "1";
    star.style.transform = "translate(-50%, -50%) scale(1.5) rotate(360deg)";
  }, 50);
  setTimeout(() => { star.remove(); }, 1000);
}

function showMatchPopup(matchName) {
  const popup = document.createElement("div");
  popup.className = "match-popup";
  popup.innerHTML = `
    <div class="content">
      <i class="fas fa-heart text-5xl text-emerald-500 mb-4 animate-bounce"></i>
      <h2>It's a Match!</h2>
      <p>You and ${matchName} liked each other.</p>
      <button onclick="this.parentElement.parentElement.remove()" class="mt-4 px-6 py-2 bg-emerald-500 text-white rounded-full font-bold hover:bg-emerald-600 transition">Keep Swiping</button>
    </div>
  `;

  // Basic styles
  Object.assign(popup.style, {
    position: 'fixed',
    top: '0', left: '0', width: '100%', height: '100%',
    backgroundColor: 'rgba(0,0,0,0.85)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: '3000', opacity: '0', transition: 'opacity 0.3s ease'
  });

  const content = popup.querySelector('.content');
  Object.assign(content.style, {
    textAlign: 'center', color: 'white', padding: '2rem',
    backgroundColor: '#1a1a1a', borderRadius: '1rem', border: '1px solid #333',
    minWidth: '300px'
  });

  document.body.appendChild(popup);

  requestAnimationFrame(() => {
    popup.style.opacity = '1';
  });
}
