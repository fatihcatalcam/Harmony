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

async function loadProfilesToLike() {
    try {
        const response = await fetch("/api/get_profiles");
        if (!response.ok) {
            throw new Error("Failed to fetch profiles");
        }
        const profiles = await response.json();

        if (!profiles || profiles.length === 0) {
            profilesContainer.innerHTML = "<p>No profiles available to like! Try again later.</p>";
            return;
        }

        profilesContainer.innerHTML = ""; // Clear existing profiles
        profiles.forEach((profile) => {
            const profileCard = `
                <div class="profile-card">
                    <img src="${profile.profile_image}" alt="Profile Picture">
                    <h3>${profile.display_name}</h3>
                    <p><strong>Top Artists:</strong> ${profile.top_artists.join(", ")}</p>
                    <p><strong>Top Genres:</strong> ${profile.genres.join(", ")}</p>
                    <p><strong>Top Tracks:</strong> ${profile.top_tracks.join(", ")}</p>
                    <button class="like-btn" data-profile-id="${profile.id}">Like</button>
                    <button class="btn pass-btn" data-profile-id="${profile.id}">Pass</button>
                </div>`;
            profilesContainer.innerHTML += profileCard;
        });
    } catch (error) {
        profilesContainer.innerHTML = "<p>Error loading profiles. Please try again later.</p>";
        console.error("Error fetching profiles:", error);
    }
}

profilesContainer.addEventListener("click", (e) => {
    const target = e.target;

    // Like Button Clicked
    if (target.classList.contains("like-btn")) {
        const profileId = target.dataset.profileId;
        likeProfile(profileId);
    }

    // Pass Button Clicked
    if (target.classList.contains("pass-btn")) {
        const profileId = target.dataset.profileId;
        passProfile(profileId);
    }
});

async function likeProfile(profileId) {
    try {
        const response = await fetch("/api/like_profile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ profile_id: profileId }),
        });

        const result = await response.json();
        if (result.message === "It's a match!") {
            alert("You've got a match! 🎉");
        } else if (result.message === "Profile liked!") {
            alert("Profile liked!");
        } else {
            alert(result.error || "Something went wrong.");
        }

        loadProfilesToLike(); // Reload profiles
    } catch (error) {
        console.error("Error liking profile:", error);
        alert("An error occurred while liking the profile. Please try again.");
    }
}

function passProfile(profileId) {
    alert(`You passed on profile ID: ${profileId}`);
    loadProfilesToLike(); // Reload profiles
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

