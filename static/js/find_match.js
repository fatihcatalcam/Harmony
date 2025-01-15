// DOM Element Selections
const profilesContainer = document.getElementById("profiles-container");
let currentProfileIndex = 0; // To track the current profile
let profiles = []; // Array to store profiles

// Fetch Profiles and Initialize
document.addEventListener("DOMContentLoaded", async () => {
    try {
        // Fetch profiles from the server
        const response = await fetch("/api/get_profiles");
        profiles = await response.json();

        if (profiles.length === 0) {
            profilesContainer.innerHTML = `
                <p class="text-center text-gray-500">There are no more profiles to like. Try again later!</p>
            `;
            return;
        }

        // Show the first profile
        showProfile(currentProfileIndex);
    } catch (error) {
        console.error("Error loading profiles:", error);
        profilesContainer.innerHTML = `
            <p class="text-center text-gray-500">An error occurred while loading profiles. Please try again later!</p>
        `;
    }
});

// Function to Show a Single Profile
function showProfile(index) {
    profilesContainer.innerHTML = ""; // Clear previous profile

    if (index >= profiles.length) {
        profilesContainer.innerHTML = `
            <p class="text-center text-gray-500">No more profiles to display!</p>
        `;
        return;
    }

    const profile = profiles[index];
    const profileCard = document.createElement("div");
    profileCard.className = "card";

    profileCard.innerHTML = `
        <h2>${profile.display_name}</h2>
        <p><strong>Top Genres:</strong> ${profile.genres.join(", ")}</p>
        <div class="top-artists">
            <h3>Top Artists</h3>
            ${profile.top_artists.map(artist => `<p>${artist}</p>`).join("")}
        </div>
        <div class="top-tracks">
            <h3>Top Tracks</h3>
            ${profile.top_tracks.map(track => `<p>${track}</p>`).join("")}
        </div>
        <div class="actions">
            <button class="btn like" onclick="likeProfile(${profile.id})">
                <i class="fas fa-heart"></i> Like
            </button>
            <button class="btn pass" onclick="passProfile(${profile.id})">
                <i class="fas fa-times"></i> Pass
            </button>
        </div>
    `;

    profilesContainer.appendChild(profileCard);
}

// Like Profile Functionality
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
        } else {
            alert("Profile liked!");
        }

        // Show the next profile
        currentProfileIndex++;
        showProfile(currentProfileIndex);
    } catch (error) {
        console.error("Error liking profile:", error);
        alert("An error occurred. Please try again.");
    }
}

// Pass Profile Functionality
function passProfile(profileId) {
    alert(`You passed on profile ID: ${profileId}`);

    // Show the next profile
    currentProfileIndex++;
    showProfile(currentProfileIndex);
}
