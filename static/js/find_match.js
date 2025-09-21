/***********************************************************
 * find_match_interact.js - Interact.js ile Tinder-Style Swipe & Animasyonlar
 ***********************************************************/

// DOMContentLoaded: Kartları hazırla, draggable yap ve Interact.js ile sürükleme mantığını başlat.
document.addEventListener("DOMContentLoaded", function() {
  const container = document.querySelector(".container");
  const cards = Array.from(document.querySelectorAll(".card"));

  if (!cards || cards.length === 0) {
    container.innerHTML = `<p class="text-center text-gray-500">No profiles to display!</p>`;
    return;
  }

  // Her kart için başlangıç kümülatif dx ve dy değerlerini sıfırlıyoruz.
  cards.forEach(card => {
    card.currentDx = 0; // kümülatif x yönü
    card.currentDy = 0; // kümülatif y yönü
    card.style.touchAction = "none"; // dokunmatik cihazlarda default scroll davranışını engelle
  });

  // Interact.js ile kartları draggable yapıyoruz.
  interact('.card').draggable({
    inertia: true,
    listeners: {
      move: dragMoveListener,
      end: dragEndListener
    }
  });
  

  // Sürükleme hareketi sırasında çalışan fonksiyon
  function dragMoveListener(event) {
    const target = event.target;
    // Kümülatif dx ve dy değerlerine, o anki hareket miktarını ekliyoruz.
    target.currentDx = (target.currentDx || 0) + event.dx;
    target.currentDy = (target.currentDy || 0) + event.dy;
    // Debug log: Her hareket adımındaki dx, dy ve toplam x
    console.log(`dragMoveListener: dx: ${event.dx} dy: ${event.dy} cumulative x: ${target.currentDx}`);
    target.style.transform = `translate(${target.currentDx}px, ${target.currentDy}px)`;
  }

  // Sürükleme bittiğinde çalışan fonksiyon
  async function dragEndListener(event) {
    const target = event.target;
  
    // gerçek konumu CSS transformdan al
    const style = window.getComputedStyle(target);
    const matrix = new DOMMatrixReadOnly(style.transform);
    const cumulativeX = matrix.m41;
  
    console.log("Gerçek cumulativeX:", cumulativeX);
  
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
  
  

  // Kartı sağa fırlatarak "like" işlemi yapan fonksiyon
  async function handleLike(card) {
    card.style.transition = "transform 0.5s";
    card.style.transform = "translate(400px, 0px) rotate(30deg)";
    const profileId = card.getAttribute("data-id");
    
    console.log("Like edilen profil ID:", profileId); // Bunu mutlaka ekle
    
    try {
      const res = await fetch("/api/like_profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile_id: profileId })
      });
  
      if (!res.ok) throw new Error(`Failed to like profile: ${res.statusText}`);
      const result = await res.json();
      
      console.log("Backend response:", result); // Backend'den gelen cevabı gör
  
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
  

  // Kartı sola fırlatarak "pass" işlemi yapan fonksiyon
  function handlePass(card) {
    card.style.transition = "transform 0.5s";
    card.style.transform = "translate(-400px, 0px) rotate(-30deg)";
    showCross();
    setTimeout(() => {
      card.remove();
      checkEmptyStack();
    }, 500);
  }

  // Eğer tüm kartlar kaldırılmışsa, container'a mesaj ekler.
  function checkEmptyStack() {
    const remaining = container.querySelectorAll(".card");
    if (remaining.length === 0) {
      container.innerHTML = `<p class="text-center text-gray-500">No more profiles!</p>`;
    }
  }

  // Opsiyonel: Kart üzerindeki like/pass butonlarına click event ekleyelim.
  cards.forEach(card => {
    const passBtn = card.querySelector(".btn.pass");
    const likeBtn = card.querySelector(".btn.like");
  
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
  });
  
  
});

/***********************************************************
 * Animasyon Fonksiyonları
 ***********************************************************/
function showHeart() {
  const heart = document.createElement("div");
  heart.className = "heart-animation";
  // Stil ve içerik: Kalp simgesi, örneğin Font Awesome kullanarak
  heart.innerHTML = "<i class='fas fa-heart' style='font-size: 80px; color: rgba(255,255,255,0.8);'></i>";
  // Merkezi ve üstte overlay gibi gösterim için konumlandırma
  heart.style.position = "fixed";
  heart.style.top = "50%";
  heart.style.left = "50%";
  heart.style.transform = "translate(-50%, -50%)";
  heart.style.zIndex = "2000";
  heart.style.opacity = "0";
  heart.style.transition = "opacity 0.5s ease, transform 0.5s ease";
  document.body.appendChild(heart);
  // Animasyonu tetikleyelim
  setTimeout(() => {
    heart.style.opacity = "1";
    heart.style.transform = "translate(-50%, -50%) scale(1.2)";
  }, 50);
  // Animasyon bittikten sonra kaldır
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
