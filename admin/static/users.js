// admin/static/users.js

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}

async function loadPending() {
  const data = await apiFetch("/api/admin/users?approval_status=pending");
  const card = document.getElementById("pending-card");
  const tbody = document.getElementById("pending-tbody");
  tbody.innerHTML = "";

  if (!data.items.length) {
    card.style.display = "none";
    return;
  }
  card.style.display = "block";

  data.items.forEach((u) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(u.full_name)}</td>
      <td>${escapeHtml(u.department || "-")}</td>
      <td><span class="badge badge-pending">Ожидает решения</span></td>
      <td>${escapeHtml(u.phone || "-")}</td>
      <td class="text-right">
        <button class="btn btn-success btn-sm" data-approve="${u.id}">Одобрить</button>
        <button class="btn btn-danger btn-sm" data-reject="${u.id}">Отклонить</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll("[data-approve]").forEach((btn) => {
    btn.addEventListener("click", () => decideRegistration(btn.dataset.approve, "approve"));
  });
  tbody.querySelectorAll("[data-reject]").forEach((btn) => {
    btn.addEventListener("click", () => decideRegistration(btn.dataset.reject, "reject"));
  });
}

async function decideRegistration(userId, action) {
  const label = action === "approve" ? "одобрить" : "отклонить";
  if (!window.confirm(`Точно ${label} регистрацию?`)) return;
  try {
    await apiFetch(`/api/admin/users/${userId}/${action}`, { method: "POST" });
    showToast(action === "approve" ? "Регистрация одобрена" : "Регистрация отклонена");
    loadPending();
    loadUsers();
  } catch (e) {
    showToast(humanizeError(e), "error");
  }
}

async function loadUsers() {
  const params = new URLSearchParams();
  const search = document.getElementById("f-search").value.trim();
  const role = document.getElementById("f-role").value;
  const department = document.getElementById("f-department").value;
  const active = document.getElementById("f-active").value;
  if (search) params.set("search", search);
  if (role) params.set("role", role);
  if (department) params.set("department", department);
  if (active) params.set("is_active", active);

  const data = await apiFetch(`/api/admin/users?${params.toString()}`);
  const tbody = document.getElementById("users-tbody");
  const empty = document.getElementById("users-empty");
  tbody.innerHTML = "";

  const items = data.items.filter((u) => u.approval_status !== "pending");
  empty.style.display = items.length ? "none" : "block";

  items.forEach((u) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><a href="${window.BASE_PATH}/admin/users/${u.id}">${escapeHtml(u.full_name)}</a></td>
      <td>${escapeHtml(u.role_label)}</td>
      <td>${escapeHtml(u.department || "-")}</td>
      <td>${u.vacation_days_balance ?? "-"}</td>
      <td>${u.is_active ? '<span class="badge badge-success">Активен</span>' : '<span class="badge badge-neutral">Неактивен</span>'}</td>
      <td class="text-right"><a class="btn btn-ghost btn-sm" href="${window.BASE_PATH}/admin/users/${u.id}">Открыть</a></td>
    `;
    tbody.appendChild(tr);
  });
}

// --- Создание сотрудника в справочнике (п.7 ТЗ) ---
function setupCreateUser() {
  const card = document.getElementById("create-card");
  const toggleBtn = document.getElementById("btn-toggle-create");
  const cancelBtn = document.getElementById("btn-cancel-create");
  const form = document.getElementById("create-user-form");
  if (!card || !toggleBtn || !form) return;

  toggleBtn.addEventListener("click", () => {
    card.style.display = card.style.display === "none" ? "block" : "none";
  });
  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => {
      form.reset();
      card.style.display = "none";
    });
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const payload = {
      full_name: (fd.get("full_name") || "").trim(),
      department: fd.get("department") || null,
      position: (fd.get("position") || "").trim() || null,
      role: fd.get("role") || "employee",
      manager_id: fd.get("manager_id") ? parseInt(fd.get("manager_id"), 10) : null,
      hire_date: (fd.get("hire_date") || "").trim() || null,
      birth_date: (fd.get("birth_date") || "").trim() || null,
    };
    if (!payload.full_name) {
      showToast("Укажите ФИО сотрудника", "error");
      return;
    }
    try {
      const created = await apiFetch("/api/admin/users", { method: "POST", json: payload });
      showToast(`Сотрудник «${created.full_name}» добавлен в справочник`);
      form.reset();
      card.style.display = "none";
      loadUsers();
    } catch (err) {
      showToast(humanizeError(err), "error");
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadPending();
  loadUsers();
  setupCreateUser();
  document.getElementById("btn-filter").addEventListener("click", loadUsers);
  document.getElementById("f-search").addEventListener("keydown", (e) => {
    if (e.key === "Enter") loadUsers();
  });
});
