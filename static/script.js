// Wait until the HTML page is fully loaded before running any code
document.addEventListener("DOMContentLoaded", () => {


// ==========================================
  // SHARED NAVIGATION BAR
  // ==========================================
  const navPlaceholder = document.getElementById("navbar-placeholder");
  if (navPlaceholder) {
    // Check which HTML page is currently open
    const currentPage = window.location.pathname;

    // Highlight "My Tickets" if the user is on myTickets, ticketDetails, or either ticketForm
    const isTicketsSection = [
      "/myTickets",
      "/ticketDetails",
      "/repairTicket",
      "/communityComplaint"
    ].includes(currentPage);

    navPlaceholder.innerHTML = `
      <header class="navbar">
        <div class="nav-container">
          <div class="brand">BV Housing</div>
          <nav class="nav-links">
            <a href="/home" class="nav-link ${currentPage === "/home" ? "active" : ""}">Home</a>
            <a href="/myTickets" class="nav-link ${isTicketsSection ? "active" : ""}">My Tickets</a>
            <form method="post" action="/logout" class="logout-form">
              <button type="submit" class="nav-link nav-logout">Log out</button>
            </form>
          </nav>
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
  // 4. BONUS: LOGIC FOR TICKET DETAILS PAGE
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

});