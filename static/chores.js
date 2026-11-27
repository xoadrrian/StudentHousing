// ==========================================
// CHORES (shared chores with rotation)
// Talks to the backend at /api/chores
// ==========================================
document.addEventListener("DOMContentLoaded", () => {

  // "2026-12-01" for a date, using the local day (not UTC)
  function toISO(d) {
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${d.getFullYear()}-${month}-${day}`;
  }

  // "Mon 1 Dec"
  function niceDate(iso) {
    return new Date(iso + "T00:00").toLocaleDateString("en-GB", {
      weekday: "short", day: "numeric", month: "short",
    });
  }

  // "1 Dec"
  function shortDate(d) {
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  }

  const STATE_TEXT = { done: "Done ✓", open: "To do", overdue: "Overdue", upcoming: "Planned" };

  // ---------- HOME PAGE: week bar + list for the chosen day ----------
  const weekBar = document.getElementById("week-selector");
  const dayList = document.getElementById("chore-tasks-container");
  let reloadWeek = () => {};
  let reloadTodo = () => {};

  if (weekBar && dayList) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const thisMonday = new Date(today);
    thisMonday.setDate(today.getDate() - ((today.getDay() + 6) % 7)); // go back to Monday

    const dayButtons = [...weekBar.querySelectorAll(".day-item")];
    const weekLabel = document.getElementById("week-label");
    let weekOffset = 0; // 0 = this week, 1 = next week, -1 = last week
    let monday = thisMonday;
    let week = [];
    let selected = toISO(today);

    // Each day button gets a little row for dots
    dayButtons.forEach((button) => {
      const dots = document.createElement("span");
      dots.className = "day-dots";
      button.appendChild(dots);
      button.addEventListener("click", () => selectDay(button.dataset.date));
    });

    function showWeek() {
      monday = new Date(thisMonday);
      monday.setDate(thisMonday.getDate() + weekOffset * 7);
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);
      if (weekLabel) weekLabel.textContent = `${shortDate(monday)} – ${shortDate(sunday)}`;

      dayButtons.forEach((button, i) => {
        const d = new Date(monday);
        d.setDate(monday.getDate() + i);
        button.dataset.date = toISO(d);
        button.querySelector(".day-number").textContent = d.getDate();
        button.classList.toggle("today", toISO(d) === toISO(today));
      });

      // This week: select today. Other weeks: select Monday.
      selected = weekOffset === 0 ? toISO(today) : toISO(monday);
      reloadWeek();
    }

    function selectDay(iso) {
      selected = iso;
      dayButtons.forEach((b) => b.classList.toggle("active", b.dataset.date === iso));
      renderDay();
    }

    function drawDots() {
      dayButtons.forEach((button) => {
        const dots = button.querySelector(".day-dots");
        dots.innerHTML = "";
        week
          .filter((x) => x.date === button.dataset.date)
          .slice(0, 3) // at most 3 dots per day
          .forEach((x) => {
            const dot = document.createElement("span");
            dot.className = "day-dot " + x.state;
            dots.appendChild(dot);
          });
      });
    }

    function renderDay() {
      dayList.innerHTML = "";
      const items = week.filter((x) => x.date === selected);
      if (items.length === 0) {
        dayList.innerHTML = '<p class="empty-note">No chores this day.</p>';
        return;
      }
      for (const x of items) {
        const row = document.createElement("div");
        row.className = "chore-row";

        // Left: chore name, and how often it repeats underneath
        const main = document.createElement("span");
        main.className = "chore-main";
        const title = document.createElement("span");
        title.textContent = x.title;
        const repeats = document.createElement("small");
        repeats.className = "chore-sub";
        repeats.textContent = x.repeats;
        main.append(title, repeats);

        // Middle: whose turn, and who is next underneath
        const who = document.createElement("span");
        who.className = "chore-who";
        const now = document.createElement("span");
        now.textContent = x.is_mine ? "You" : x.person_name;
        if (x.is_mine) now.className = "chore-mine";
        who.appendChild(now);
        if (x.next_name) {
          const next = document.createElement("small");
          next.className = "chore-sub";
          next.textContent = "Next: " + x.next_name;
          who.appendChild(next);
        }

        const state = document.createElement("span");
        state.className = "chore-state " + x.state;
        state.textContent = STATE_TEXT[x.state];

        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "supply-delete";
        remove.textContent = "×";
        remove.title = "Remove chore";
        remove.addEventListener("click", async () => {
          if (!confirm(`Remove "${x.title}" for everyone?`)) return;
          await fetch(`/api/chores/${x.chore_id}`, { method: "DELETE" });
          reloadWeek();
          reloadTodo();
        });

        row.append(main, who, state, remove);
        dayList.appendChild(row);
      }
    }

    reloadWeek = async () => {
      const res = await fetch(`/api/chores/week?start=${toISO(monday)}`);
      if (!res.ok) return;
      week = await res.json();
      drawDots();
      selectDay(selected);
    };

    document.getElementById("week-prev")?.addEventListener("click", () => {
      weekOffset -= 1;
      showWeek();
    });
    document.getElementById("week-next")?.addEventListener("click", () => {
      weekOffset += 1;
      showWeek();
    });

    showWeek();
  }

  // ---------- HOME PAGE: my To Do list ----------
  const todoList = document.getElementById("to-do-list");
  const doneButton = document.getElementById("btn-mark-done");

  if (todoList) {
    reloadTodo = async () => {
      const res = await fetch("/api/chores/todo");
      if (!res.ok) return;
      const turns = await res.json();

      todoList.innerHTML = "";
      if (turns.length === 0) {
        todoList.innerHTML = '<p class="empty-note">Nothing to do 🎉</p>';
      }
      for (const t of turns) {
        const label = document.createElement("label");
        label.className = "todo-item";

        const box = document.createElement("input");
        box.type = "checkbox";
        box.value = t.turn_id;

        const title = document.createElement("span");
        title.textContent = t.title;

        const due = document.createElement("span");
        due.className = t.overdue ? "todo-due overdue" : "todo-due";
        due.textContent = niceDate(t.due_date) + (t.overdue ? " · late" : "");

        label.append(box, title, due);
        todoList.appendChild(label);
      }
    };

    if (doneButton) {
      doneButton.addEventListener("click", async () => {
        const ticked = todoList.querySelectorAll("input[type=checkbox]:checked");
        for (const box of ticked) {
          await fetch(`/api/chores/turns/${box.value}/done`, { method: "POST" });
        }
        reloadTodo();
        reloadWeek();
      });
    }

    reloadTodo();
  }

  // ---------- ADD CHORE PAGE ----------
  const choreForm = document.getElementById("add-chore-form");
  const pills = document.getElementById("tenant-pills-container");

  if (choreForm && pills) {
    const dayPills = document.getElementById("weekday-pills");
    const peopleError = document.getElementById("people-error");
    const daysError = document.getElementById("days-error");

    async function loadHousemates() {
      const res = await fetch("/api/inventory/tenants");
      if (!res.ok) return;
      const tenants = await res.json();

      pills.innerHTML = "";
      for (const t of tenants) {
        const label = document.createElement("label");
        label.className = "tenant-pill";

        const box = document.createElement("input");
        box.type = "checkbox";
        box.name = "member_ids";
        box.value = t.id;

        const name = document.createElement("span");
        name.textContent = t.name;

        label.append(box, name);
        pills.appendChild(label);
      }
    }

    // One button that ticks all / unticks all boxes in a group
    function makeToggle(button, group, allText, noneText) {
      if (!button || !group) return;
      const boxes = () => [...group.querySelectorAll("input[type=checkbox]")];
      const allTicked = () => boxes().length > 0 && boxes().every((b) => b.checked);
      const updateText = () => { button.textContent = allTicked() ? noneText : allText; };
      button.addEventListener("click", () => {
        const tick = !allTicked();
        boxes().forEach((b) => { b.checked = tick; });
        updateText();
      });
      group.addEventListener("change", updateText);
    }

    makeToggle(document.getElementById("btn-select-all"), pills, "[Select All]", "[Deselect All]");
    makeToggle(document.getElementById("btn-every-day"), dayPills, "[Every day]", "[Clear days]");

    // Hide an error as soon as something is ticked
    pills.addEventListener("change", () => { if (peopleError) peopleError.hidden = true; });
    dayPills?.addEventListener("change", () => { if (daysError) daysError.hidden = true; });

    choreForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      // Check first: at least one person and one day
      const hasPerson = pills.querySelector("input:checked") !== null;
      const hasDay = dayPills?.querySelector("input:checked") !== null;
      if (peopleError) peopleError.hidden = hasPerson;
      if (daysError) daysError.hidden = hasDay;
      if (!hasPerson || !hasDay) return;

      const res = await fetch("/api/chores", {
        method: "POST",
        body: new FormData(choreForm),
      });
      if (res.ok) {
        window.location.href = "/home";
      } else {
        const error = await res.json();
        alert(error.detail || "Could not save the chore.");
      }
    });

    loadHousemates();
  }
});