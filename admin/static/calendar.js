// admin/static/calendar.js

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}

function formatDate(iso) {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric", weekday: "short" });
}

function populateYears() {
  const select = document.getElementById("f-year");
  for (let y = CURRENT_YEAR - 2; y <= CURRENT_YEAR + 3; y++) {
    const opt = document.createElement("option");
    opt.value = y;
    opt.textContent = y;
    if (y === CURRENT_YEAR) opt.selected = true;
    select.appendChild(opt);
  }
}

async function loadCalendar() {
  const year = document.getElementById("f-year").value;
  const month = document.getElementById("f-month").value;
  const params = new URLSearchParams();
  if (year) params.set("year", year);
  if (month) params.set("month", month);

  const data = await apiFetch(`/api/admin/calendar?${params.toString()}`);
  const tbody = document.getElementById("calendar-tbody");
  const empty = document.getElementById("calendar-empty");
  tbody.innerHTML = "";
  empty.style.display = data.items.length ? "none" : "block";

  data.items.forEach((d) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${formatDate(d.date)}</td>
      <td>${d.is_workday ? '<span class="badge badge-progress">Рабочий</span>' : '<span class="badge badge-neutral">Нерабочий</span>'}</td>
      <td>${escapeHtml(d.description || "-")}</td>
      <td class="text-right"><button class="btn btn-danger btn-sm" data-delete-id="${d.id}" data-confirm="Удалить запись за ${formatDate(d.date)}?">Удалить</button></td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll("[data-delete-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await apiFetch(`/api/admin/calendar/${btn.dataset.deleteId}`, { method: "DELETE" });
        showToast("Запись удалена");
        loadCalendar();
      } catch (e) {
        showToast(humanizeError(e), "error");
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  populateYears();
  loadCalendar();

  document.getElementById("btn-filter").addEventListener("click", loadCalendar);

  document.getElementById("btn-single-add").addEventListener("click", () => {
    document.getElementById("modal-single").classList.add("open");
  });
  document.getElementById("btn-bulk-add").addEventListener("click", () => {
    document.getElementById("modal-bulk").classList.add("open");
  });
  document.querySelectorAll("[data-close-modal]").forEach((btn) => {
    btn.addEventListener("click", () => document.getElementById(btn.dataset.closeModal).classList.remove("open"));
  });

  document.getElementById("modal-single-submit").addEventListener("click", async () => {
    const date = document.getElementById("single-date").value;
    if (!date) { showToast("Укажите дату", "error"); return; }
    const payload = {
      date,
      is_workday: document.getElementById("single-workday").checked,
      description: document.getElementById("single-desc").value.trim() || null,
    };
    try {
      await apiFetch("/api/admin/calendar", { method: "POST", json: payload });
      showToast("День добавлен");
      document.getElementById("modal-single").classList.remove("open");
      loadCalendar();
    } catch (e) {
      showToast(humanizeError(e), "error");
    }
  });

  document.getElementById("modal-bulk-submit").addEventListener("click", async () => {
    const date_from = document.getElementById("bulk-from").value;
    const date_to = document.getElementById("bulk-to").value;
    if (!date_from || !date_to) { showToast("Укажите обе даты", "error"); return; }
    const payload = {
      date_from, date_to,
      is_workday: document.getElementById("bulk-workday").checked,
      description: document.getElementById("bulk-desc").value.trim() || null,
    };
    try {
      const res = await apiFetch("/api/admin/calendar/bulk", { method: "POST", json: payload });
      showToast(`Добавлено дней: ${res.created}${res.skipped ? `, пропущено (уже были): ${res.skipped}` : ""}`);
      document.getElementById("modal-bulk").classList.remove("open");
      loadCalendar();
    } catch (e) {
      showToast(humanizeError(e), "error");
    }
  });
});
