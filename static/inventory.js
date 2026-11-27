document.addEventListener("DOMContentLoaded", () => {

  const suppliesList = document.getElementById("shared-supplies-list");
  const toBuyList = document.getElementById("to-buy-list");
  const boughtButton = document.getElementById("btn-mark-bought");

  if (suppliesList && toBuyList) {

    async function loadSupplies() {
      const res = await fetch("/api/inventory");
      if (!res.ok) return;
      const items = await res.json();

      suppliesList.innerHTML = "";
      if (items.length === 0) {
        suppliesList.innerHTML = '<p class="empty-note">No supplies yet.</p>';
      }
      for (const item of items) {
        const row = document.createElement("div");
        row.className = "supply-row";

        const name = document.createElement("span");
        name.textContent = item.name;

        const who = document.createElement("span");
        who.className = "supply-who";
        const now = document.createElement("span");
        now.textContent = item.responsible_name || "—";
        who.appendChild(now);
        if (item.next_name) {
          const next = document.createElement("small");
          next.className = "supply-next";
          next.textContent = "Next: " + item.next_name;
          who.appendChild(next);
        }

        const status = document.createElement("span");
        if (item.status === "to_buy") {
          const bought = document.createElement("button");
          bought.type = "button";
          bought.className = "supply-status to-buy";
          bought.textContent = "Out of stock";
          bought.title = "Click when someone bought it";
          bought.addEventListener("click", async () => {
            await fetch(`/api/inventory/${item.id}/bought`, { method: "POST" });
            loadSupplies();
          });
          status.appendChild(bought);
        } else {
          const ranOut = document.createElement("button");
          ranOut.type = "button";
          ranOut.className = "supply-status in-stock";
          ranOut.textContent = "In stock";
          ranOut.title = "Click when it runs out";
          ranOut.addEventListener("click", async () => {
            await fetch(`/api/inventory/${item.id}/to-buy`, { method: "POST" });
            loadSupplies();
          });
          status.appendChild(ranOut);
        }

        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "supply-delete";
        remove.textContent = "×";
        remove.title = "Remove item";
        remove.addEventListener("click", async () => {
          if (!confirm(`Remove "${item.name}" from the list?`)) return;
          await fetch(`/api/inventory/${item.id}`, { method: "DELETE" });
          loadSupplies();
        });

        row.append(name, who, status, remove);
        suppliesList.appendChild(row);
      }

      // 2. To Buy list: only items that ran out AND are my job
      const myShopping = items.filter((i) => i.status === "to_buy" && i.is_mine);
      toBuyList.innerHTML = "";
      if (myShopping.length === 0) {
        toBuyList.innerHTML = '<p class="empty-note">Nothing to buy 🎉</p>';
      }
      for (const item of myShopping) {
        const label = document.createElement("label");
        label.className = "to-buy-item";

        const box = document.createElement("input");
        box.type = "checkbox";
        box.value = item.id;

        const text = document.createElement("span");
        text.textContent = item.name;

        label.append(box, text);
        toBuyList.appendChild(label);
      }
    }

    // "Mark as Bought": send every ticked item to the backend, then refresh
    if (boughtButton) {
      boughtButton.addEventListener("click", async () => {
        const ticked = toBuyList.querySelectorAll("input[type=checkbox]:checked");
        for (const box of ticked) {
          await fetch(`/api/inventory/${box.value}/bought`, { method: "POST" });
        }
        loadSupplies();
      });
    }

    loadSupplies();
  }


  // ---------- ADD ITEM PAGE ----------
  const addForm = document.getElementById("add-item-form");
  const pills = document.getElementById("tenant-pills-container");

  if (addForm && pills) {

    // Fill the "Who takes turns?" choices with my housemates
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

        // "Select All" / "Deselect All": one button that switches
    const selectAll = document.getElementById("btn-select-all");

    function allTicked() {
      const boxes = [...pills.querySelectorAll("input[type=checkbox]")];
      return boxes.length > 0 && boxes.every((box) => box.checked);
    }

    function updateSelectAllText() {
      selectAll.textContent = allTicked() ? "[Deselect All]" : "[Select All]";
    }

    if (selectAll) {
      selectAll.addEventListener("click", () => {
        const tick = !allTicked();
        pills.querySelectorAll("input[type=checkbox]").forEach((box) => {
          box.checked = tick;
        });
        updateSelectAllText();
      });
      pills.addEventListener("change", updateSelectAllText);
    }

    // Save: send the form to the backend, then go back home
    addForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      // Check first: at least one person ticked
      const peopleError = document.getElementById("people-error");
      const hasPerson = pills.querySelector("input:checked") !== null;
      if (peopleError) peopleError.hidden = hasPerson;
      if (!hasPerson) return;

      const res = await fetch("/api/inventory", {
        method: "POST",
        body: new FormData(addForm),
      });
      if (res.ok) {
        window.location.href = "/home";
      } else {
        const error = await res.json();
        alert(error.detail || "Could not save the item.");
      }
    });

    loadHousemates();
  }
});

