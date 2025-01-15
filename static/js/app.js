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

// Login Button Hover Animation
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


// Find Your Match Button Functionality
if (findMatchBtn) {
    findMatchBtn.addEventListener("click", async () => {
        const userId = findMatchBtn.dataset.userId;
        try {
            const response = await fetch(`/matches/${userId}`);
            const data = await response.json();

            if (data.matches && data.matches.length > 0) {
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

// Scroll-Based Background Darkening Effect
window.addEventListener("scroll", () => {
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const maxDarkness = 0.85;
    const opacity = Math.min(scrollTop / 500, maxDarkness);
    document.body.style.background = `linear-gradient(135deg, rgba(29, 185, 84, ${1 - opacity}), rgba(25, 20, 20, ${1}))`;
});

const matchesList = document.querySelector('.matches-list');
const matches = [
  { profile_image: 'https://placehold.co/80x80', display_name: 'User 1' },
  { profile_image: 'https://placehold.co/80x80', display_name: 'User 2' },
];

matches.forEach(match => {
  const card = document.createElement('div');
  card.classList.add('match-card');

  card.innerHTML = `
    <img src="${match.profile_image}" alt="${match.display_name}" />
    <p>${match.display_name}</p>
  `;

  matchesList.appendChild(card);
});
