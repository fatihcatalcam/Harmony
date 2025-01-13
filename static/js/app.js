// DOM Elementlerini Seç
const profilePic = document.getElementById("profile-pic");
const loginBtn = document.getElementById("login-btn");
const logoutBtn = document.getElementById("logout-btn");
const findMatchBtn = document.getElementById("find-match-btn");

// Sayfa Yüklenirken Animasyonlar
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

// Login Butonu Hover Animasyonu
if (loginBtn) {
    loginBtn.addEventListener("mouseover", () => {
        loginBtn.style.boxShadow = "0 4px 15px rgba(29, 185, 84, 0.5)";
        loginBtn.style.transform = "scale(1.1)";
    });

    loginBtn.addEventListener("mouseout", () => {
        loginBtn.style.boxShadow = "none";
        loginBtn.style.transform = "scale(1)";
    });
}

// Profil fotoğrafına tıklama animasyonu ve yönlendirme
if (profilePic) {
    profilePic.addEventListener("click", () => {
        profilePic.style.transition = "transform 0.2s ease";
        profilePic.style.transform = "scale(0.9)";
        setTimeout(() => {
            profilePic.style.transform = "scale(1)";
            window.location.href = "/profile"; // Top sanatçıların ve şarkıların olduğu profil sayfasına yönlendir
        }, 150);
    });
}

// Logout Butonu İşlemleri
if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
        e.preventDefault(); // Sayfanın hemen yeniden yüklenmesini engelle
        logoutBtn.innerText = "Logging out...";
        logoutBtn.style.backgroundColor = "#f44336"; // Kırmızı renk
        logoutBtn.style.transition = "background-color 0.3s ease, transform 0.3s ease";
        logoutBtn.style.transform = "scale(0.95)";
        setTimeout(() => {
            window.location.href = "/logout"; // Logout işlemine yönlendir
        }, 500);
    });
}

// Find Your Match Butonu Hover ve Tıklama Animasyonu
if (findMatchBtn) {
    findMatchBtn.addEventListener("mouseover", () => {
        findMatchBtn.style.background = "#1aa34a";
        findMatchBtn.style.boxShadow = "0 4px 15px rgba(29, 185, 84, 0.5)";
        findMatchBtn.style.transform = "scale(1.05)";
    });

    findMatchBtn.addEventListener("mouseout", () => {
        findMatchBtn.style.background = "#1db954";
        findMatchBtn.style.boxShadow = "none";
        findMatchBtn.style.transform = "scale(1)";
    });

    findMatchBtn.addEventListener("click", () => {
        findMatchBtn.innerText = "Finding your match...";
        findMatchBtn.style.background = "#1aa34a";
        findMatchBtn.style.transition = "background 0.3s ease";
        setTimeout(() => {
            alert("This feature is under development! Stay tuned."); // Gelecek özellik için bilgi
        }, 500);
    });
}

// Dinamik Arka Plan Hareketi (Fare Hareketine Duyarlı)
document.body.addEventListener("mousemove", (e) => {
    const x = (e.clientX / window.innerWidth - 0.5) * 10;
    const y = (e.clientY / window.innerHeight - 0.5) * 10;
    document.body.style.backgroundPosition = `${x}px ${y}px`;
});

// Geri butonuna tıklama işlemi
const backButton = document.getElementById("back-btn");
if (backButton) {
    backButton.addEventListener("click", function () {
        window.location.href = "/dashboard"; // index1.html'e yönlendir
    });
}

// Scroll yapıldıkça arka plan kararma efekti
window.addEventListener("scroll", function () {
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const maxDarkness = 0.85; // Kararma miktarı
    const opacity = Math.min(scrollTop / 500, maxDarkness); // Yükseklik arttıkça kararma
    document.body.style.background = `linear-gradient(135deg, rgba(29, 185, 84, ${1 - opacity}), rgba(25, 20, 20, ${1}))`;
});


if (findMatchBtn) {
    findMatchBtn.addEventListener("click", async () => {
        const userId = findMatchBtn.dataset.userId; // Kullanıcı ID'sini al

        try {
            const response = await fetch(`/matches/${userId}`);
            const data = await response.json();

            if (data.matches && data.matches.length > 0) {
                // Eşleşmeleri listele
                let matchesHtml = "<h3>Your Matches:</h3><ul>";
                data.matches.forEach((match) => {
                    matchesHtml += `
                        <li>
                            <img src="${match.profile_image}" alt="${match.display_name}" style="width: 50px; height: 50px; border-radius: 50%;">
                            <span>${match.display_name}</span>
                        </li>`;
                });
                matchesHtml += "</ul>";

                document.querySelector(".container").innerHTML = matchesHtml;
            } else {
                alert("No matches found. Try liking more profiles!");
            }
        } catch (error) {
            console.error("Error fetching matches:", error);
            alert("An error occurred while finding your matches. Please try again.");
        }
    });
}

// Rastgele profilleri gösterme fonksiyonu
function showProfilesToLike(userId) {
    fetch(`/get_profiles_to_like/${userId}`)
        .then(response => response.json())
        .then(data => {
            if (data.profiles && data.profiles.length > 0) {
                const profilesContainer = document.getElementById("profiles-container");
                profilesContainer.innerHTML = ""; // Önce mevcut içeriği temizle
                
                data.profiles.forEach(profile => {
                    const profileCard = document.createElement("div");
                    profileCard.classList.add("profile-card");

                    profileCard.innerHTML = `
                        <img src="${profile.profile_image}" alt="${profile.display_name}" />
                        <h3>${profile.display_name}</h3>
                        <button class="btn like-btn" data-user-id="${profile.id}">Like</button>
                    `;

                    profilesContainer.appendChild(profileCard);
                });

                // Like butonlarına event listener ekle
                document.querySelectorAll(".like-btn").forEach(button => {
                    button.addEventListener("click", (e) => {
                        const toUserId = e.target.dataset.userId;
                        likeProfile(userId, toUserId);
                    });
                });
            } else {
                alert("No more profiles to show!");
            }
        })
        .catch(err => console.error("Error fetching profiles:", err));
}

// Bir profili beğenme
function likeProfile(fromUserId, toUserId) {
    fetch("/like", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ from_user_id: fromUserId, to_user_id: toUserId }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.message === "It's a match!") {
                alert("It's a match! 🎉");
            } else {
                alert(data.message);
            }
        })
        .catch(err => console.error("Error liking profile:", err));
}

// No matches found butonuna event listener ekle
document.getElementById("no-matches-btn").addEventListener("click", () => {
    const userId = document.getElementById("no-matches-btn").dataset.userId;
    showProfilesToLike(userId);
});

// static/js/app.js

function passUser() {
    fetch("/pass", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ from_user_id: 1, to_user_id: 2 })
    })
    .then(response => response.json())
    .then(data => {
      console.log(data);
      // "Pass" sonrası yapılacak işlemler
    });
  }
  
  function likeUser() {
    fetch("/like", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ from_user_id: 1, to_user_id: 2 })
    })
    .then(response => response.json())
    .then(data => {
      console.log(data);
      if (data.message === "It's a match!") {
        alert("You've got a match!");
      }
    });
  }
  