// Wait until the HTML page is fully loaded before running any code
document.addEventListener("DOMContentLoaded", () => {

  // NAVIGATION BAR
  const navPlaceholder = document.getElementById("navbar-placeholder");
  if (navPlaceholder) {
    const currentPage = window.location.pathname;
    const isTicketsSection = [
      "/myTickets",
      "/ticketDetails",
      "/repairTicket",
      "/communityComplaint"
    ].includes(currentPage);

    // Takes logged-in user info from data attributes and renders the navigation bar dynamically
    const userName = navPlaceholder.dataset.name;
    const userRole = navPlaceholder.dataset.role;

    // Automatically generate initials (e.g., "Alexandra G." -> "AG")
    const initials = userName
      .split(" ")
      .map(part => part[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);

    navPlaceholder.innerHTML = `
      <header class="navbar">
        <div class="nav-container">
          
          <!-- Left: Brand & Log Out -->
          <div class="nav-left">
            <a href="/" class="brand">BV Housing</a>
            <form method="post" action="/logout" class="logout-form">
              <button type="submit" class="nav-logout">Log out</button>
            </form>
          </div>

          <!-- Center: Navigation Links -->
          <nav class="nav-links">
            <a href="/home" class="nav-link ${currentPage === "/home" ? "active" : ""}">Home</a>
            <a href="/myTickets" class="nav-link ${isTicketsSection ? "active" : ""}">My Tickets</a>
          </nav>

          <!-- Right: User Role, Avatar & Name -->
          <div class="nav-user">
            <span class="role-badge">${userRole}</span>
            <div class="user-avatar">${initials}</div>
            <span class="user-name">${userName}</span>
          </div>

        </div>
      </header>
    `;
  }

  //  Get existing tickets from browser memory (or an empty list if none exist yet)
  function getTickets() {
    const saved = localStorage.getItem("bv_tickets");
    return saved ? JSON.parse(saved) : [];
  }

  // Save a new ticket into browser memory
  function saveTicket(newTicket) {
    const tickets = getTickets();
    tickets.push(newTicket);
    localStorage.setItem("bv_tickets", JSON.stringify(tickets));
  }

  // 1. LOGIC FOR TICKET FORM 1 (REPAIR REQUEST)
  const maintenanceForm = document.getElementById("maintenance-form");
  if (maintenanceForm) {
    maintenanceForm.addEventListener("submit", (event) => {
      event.preventDefault(); // Stop the page from reloading before we save

      const title = document.getElementById("title").value;
      const description = document.getElementById("description").value;
      const imageInput = document.getElementById("image");

      // Function to finish saving and redirect
      const finishSaving = (imageDataUrl = "") => {
        const ticket = {
          id: Date.now(), // Creates a unique ID using the current timestamp
          title: title,
          description: description,
          category: "Repair Request",
          image: imageDataUrl
        };

        saveTicket(ticket);
        window.location.href = "/myTickets"; // Go to My Tickets page
      };

      // Check if the user attached an image
      if (imageInput.files && imageInput.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
          finishSaving(e.target.result); // Save with image
        };
        reader.readAsDataURL(imageInput.files[0]);
      } else {
        finishSaving(); // Save without image
      }
    });
  }

 
  // 2. LOGIC FOR TICKET FORM 2 (COMMUNITY)

  const communityForm = document.getElementById("community-form");
  if (communityForm) {
    communityForm.addEventListener("submit", (event) => {
      event.preventDefault(); // Stop the page from reloading

      const title = document.getElementById("title").value;
      const description = document.getElementById("description").value;

      const ticket = {
        id: Date.now(),
        title: title,
        description: description,
        category: "Community Complaint",
        image: ""
      };

      saveTicket(ticket);
      window.location.href = "/myTickets"; // Go to My Tickets page
    });
  }

  
  // 3. LOGIC FOR MY TICKETS PAGE (DISPLAYING)
 
  const maintenanceList = document.getElementById("maintenance-reports-list");
  const communityList = document.getElementById("community-reports-list");

  if (maintenanceList && communityList) {
    const tickets = getTickets();

    tickets.forEach((ticket) => {
      // Create a clickable card for each ticket
      const ticketCard = document.createElement("div");
      ticketCard.className = "report-item";
      ticketCard.style.cursor = "pointer";
      ticketCard.innerHTML = `
        <h3>${ticket.title}</h3>
        <p>${ticket.description}</p>
      `;

      // Optional: When clicked, remember which ticket was clicked and open details page
      ticketCard.addEventListener("click", () => {
        localStorage.setItem("selected_ticket_id", ticket.id);
        window.location.href = "/ticketDetails"; // Matches your filename
      });

      // Put the ticket into the right column
      if (ticket.category === "Repair Request") {
        maintenanceList.appendChild(ticketCard);
      } else {
        communityList.appendChild(ticketCard);
      }
    });
  }

  // ==========================================
  // LOGIC FOR TICKET DETAILS PAGE
  // ==========================================
  const detailsContent = document.getElementById("ticket-details-content");
  if (detailsContent) {
    const selectedId = Number(localStorage.getItem("selected_ticket_id"));
    const tickets = getTickets();
    const ticket = tickets.find((t) => t.id === selectedId);

    if (ticket) {
      document.getElementById("ticket-title").textContent = ticket.title;
      document.getElementById("ticket-category").textContent = ticket.category;
      document.getElementById("ticket-description").textContent = ticket.description;

      if (ticket.image) {
        const imgSection = document.getElementById("ticket-image-section");
        const imgTag = document.getElementById("ticket-image");
        imgTag.src = ticket.image;
        imgSection.classList.remove("hidden");
      }
    }
  }

// ==========================================
  // ROOM ENVIRONMENT (live sensor data)
  // ==========================================
  const envTemp = document.getElementById("env-temp");
  if (envTemp) {
    const liveBadge = document.getElementById("sensor-live-status");
    const MAX_AGE_MINUTES = 5; // Data older than 5 minutes = Outdated

    function setStatus(id, level, text) {
      const el = document.getElementById(id);
      el.className = "env-status status-" + level;
      el.textContent = text;
    }

    function setLiveBadge(isLive) {
      if (!liveBadge) return;
      if (isLive) {
        liveBadge.className = "sensor-badge live";
        liveBadge.textContent = "● Current status";
      } else {
        liveBadge.className = "sensor-badge outdated";
        liveBadge.textContent = "● Outdated status";
      }
    }

    // Ensures UTC timestamps from Python are parsed properly
    function parseTimestamp(rawTime) {
      if (typeof rawTime === "number") {
        // Handle Unix timestamps (seconds vs milliseconds)
        return rawTime < 1e12 ? rawTime * 1000 : rawTime;
      }
      if (typeof rawTime === "string") {
        // If no timezone ("Z" or "+01:00") is present, treat it as UTC by adding "Z"
        const hasTimezone = /Z|[+-]\d{2}:?\d{2}$/.test(rawTime);
        return new Date(hasTimezone ? rawTime : rawTime + "Z").getTime();
      }
      return NaN;
    }

    async function loadEnvironment() {
      try {
        const res = await fetch("/api/sensors/my-room/latest");
        if (!res.ok) {
          setLiveBadge(false);
          return;
        }
        const r = await res.json();
        console.log("Sensor API response:", r); // Check browser Console (F12) to see exact fields

        // Look for the timestamp field in the JSON response
        const rawTime =
          r.recorded_at ||
          r.timestamp ||
          r.created_at ||
          r.updated_at ||
          r.time ||
          r.date;

        if (rawTime) {
          const readingTime = parseTimestamp(rawTime);
          const ageInMinutes = (Date.now() - readingTime) / (1000 * 60);
          setLiveBadge(!isNaN(ageInMinutes) && ageInMinutes <= MAX_AGE_MINUTES);
        } else {
          // If no timestamp exists at all, mark as Outdated instead of guessing Live
          setLiveBadge(false);
        }

        envTemp.textContent = `${Number(r.temperature_c).toFixed(1)} °C`;
        document.getElementById("env-humidity").textContent = `${Math.round(r.humidity_pct)} %`;
        document.getElementById("env-co2").textContent = `${r.co2_ppm} ppm`;

        const t = r.temperature_c;
        if (t >= 19 && t <= 24) setStatus("env-temp-status", "good", "Comfortable");
        else if (t >= 16 && t <= 27) setStatus("env-temp-status", "warning", t < 19 ? "A bit cold" : "A bit warm");
        else setStatus("env-temp-status", "alert", t < 16 ? "Too cold" : "Too hot");

        const h = r.humidity_pct;
        if (h >= 30 && h <= 60) setStatus("env-humidity-status", "good", "Good");
        else if (h >= 20 && h <= 70) setStatus("env-humidity-status", "warning", h < 30 ? "Dry" : "Humid");
        else setStatus("env-humidity-status", "alert", h < 20 ? "Very dry" : "Very humid");

        const c = r.co2_ppm;
        if (c < 1000) setStatus("env-co2-status", "good", "Fresh air");
        else if (c < 1500) setStatus("env-co2-status", "warning", "Open a window");
        else setStatus("env-co2-status", "alert", "Ventilate now");
      } catch (e) {
        console.error("Could not load sensor data", e);
        setLiveBadge(false);
      }
    }

    loadEnvironment();
    setInterval(loadEnvironment, 10000);
  }
});