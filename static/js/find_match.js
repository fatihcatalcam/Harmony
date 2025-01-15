// DOM Element Selections 
const matchProfilesContainer = document.getElementById("profiles-container");
let currentProfileIndex = 0; // To track the current profile
let profiles = []; // Array to store profiles

// Fetch Profiles and Initialize
document.addEventListener("DOMContentLoaded", async () => {
    try {
        const response = await fetch("/api/get_profiles");
        if (!response.ok) throw new Error("Failed to fetch profiles");

        profiles = await response.json();

        if (profiles.length === 0) {
            matchProfilesContainer.innerHTML = `
                <p class="text-center text-gray-500">There are no more profiles to like. Try again later!</p>
            `;
            return;
        }

        // Show the first profile
        showProfile(currentProfileIndex);
    } catch (error) {
        console.error("Error loading profiles:", error);
        matchProfilesContainer.innerHTML = `
            <p class="text-center text-gray-500">An error occurred while loading profiles. Please try again later!</p>
        `;
    }
});

function showProfile(index) {
    matchProfilesContainer.innerHTML = ""; // Clear previous profile

    if (index >= profiles.length) {
        matchProfilesContainer.innerHTML = `
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
            ${profile.top_artists
                .map(
                    artist => `
                    <div class="artist">
                        <img src="${artist.image || 'https://placehold.co/40x40'}" alt="${artist}" class="artist-img">
                        <p>${artist.name}</p>
                    </div>`
                )
                .join("")}
        </div>
        <div class="top-tracks">
            <h3>Top Tracks</h3>
            ${profile.top_tracks
                .map(
                    track => `
                    <div class="song">
                        <img src="${track.image || 'https://placehold.co/40x40'}" alt="${track}" class="track-img">
                        <p>${track.name}</p>
                    </div>`
                )
                .join("")}
        </div>
        <div class="actions">
            <button class="btn pass" id="pass-btn-${profile.id}" data-id="${profile.id}">
                <i class="fas fa-times"></i>
            </button>
            <button class="btn like" id="like-btn-${profile.id}" data-id="${profile.id}">
                <i class="fas fa-heart"></i>
            </button>
        </div>
    `;

    matchProfilesContainer.appendChild(profileCard);

    // Attach Event Listeners for Like and Pass Buttons
    document.getElementById(`like-btn-${profile.id}`).addEventListener("click", () => likeProfile(profile.id));
    document.getElementById(`pass-btn-${profile.id}`).addEventListener("click", () => passProfile(profile.id));
}



// Like Profile Functionality
async function likeProfile(profileId) {
    try {
        const response = await fetch("/api/like_profile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ profile_id: profileId }),
        });

        if (!response.ok) throw new Error("Failed to like profile");
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
