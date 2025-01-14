document.addEventListener("DOMContentLoaded", async () => {
  loadProfilesToLike(); // Call the unified function for loading profiles
});

async function loadProfilesToLike() {
  const profilesContainer = document.getElementById("profiles-container");

  try {
      const response = await fetch("/api/get_profiles");
      const profiles = await response.json();

      if (!profiles || profiles.length === 0) {
          profilesContainer.innerHTML = `
              <p class="text-center text-gray-500">There are no more profiles to like. Try again later!</p>
          `;
          return;
      }

      profilesContainer.innerHTML = ""; // Clear existing profiles

      // Render each profile as a card
      profiles.forEach((profile) => {
          const profileCard = document.createElement("div");
          profileCard.className = "card";

          profileCard.innerHTML = `
              <h2>${profile.display_name}</h2>
              <div class="top-artists">
                  <h3>Top Artists</h3>
                  ${profile.top_artists.map(artist => `<p>${artist}</p>`).join("") || "<p>No top artists available.</p>"}
              </div>
              <div class="top-tracks">
                  <h3>Top Tracks</h3>
                  ${profile.top_tracks.map(track => `<p>${track}</p>`).join("") || "<p>No top tracks available.</p>"}
              </div>
              <div class="actions">
                  <button class="btn like-btn" data-id="${profile.id}">
                      <i class="fas fa-heart"></i> Like
                  </button>
                  <button class="btn pass-btn" data-id="${profile.id}">
                      <i class="fas fa-times"></i> Pass
                  </button>
              </div>
          `;

          profilesContainer.appendChild(profileCard);
      });

      // Attach event listeners to the new buttons
      document.querySelectorAll(".like-btn").forEach(button => {
          button.addEventListener("click", () => {
              const profileId = button.getAttribute("data-id");
              likeProfile(profileId);
          });
      });

      document.querySelectorAll(".pass-btn").forEach(button => {
          button.addEventListener("click", () => {
              const profileId = button.getAttribute("data-id");
              passProfile(profileId);
          });
      });
  } catch (error) {
      console.error("Error loading profiles:", error);
      profilesContainer.innerHTML = `
          <p class="text-center text-gray-500">An error occurred while loading profiles. Please try again later!</p>
      `;
  }
}

// Like a Profile
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
          console.warn(result.error || "Unexpected response.");
      }

      // Reload profiles after liking
      loadProfilesToLike();
  } catch (error) {
      console.error("Error liking profile:", error);
      alert("An error occurred while liking the profile. Please try again.");
  }
}

// Pass a Profile
function passProfile(profileId) {
  // Optionally, implement pass API logic here
  loadProfilesToLike(); // Reload profiles after passing
}
