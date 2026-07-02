// admin/static/requests.js

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}

const OPEN_STATUSES = ["pending", "manager_approved", "in_progress"];

function statusBadgeClass(status) {
  if (status === "rejected") return "badge-danger";
  if (["hr_approved", "done"].includes(status)) return "badge-success";
  if (["manager_approved", "in_progress"].includes(status)) return "badge-progress";
  return "badge-pending";
}

function formatDate(iso) {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleDateString("ru-RU");
}

async function loadRequests() {
  const params = new URLSearchParams();
  const employee = document.getElementById("f-employee").value.trim();
  const type = document.getElementById("f-type").value;
  const dateFrom = document.getElementById("f-date-from").value;
  const dateTo = document.getElementById("f-date-to").value;
  if (employee) params.set("employee_search", employee);
  if (type) params.set("type", type);
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);

  const data = await apiFetch(`/api/admin/requests?${params.toString()}`);
  let items = data.items;

  if (document.getElementById("f-only-open").checked) {
    items = items.filter((r) => OPEN_STATUSES.includes(r.status));
  }

  const tbody = document.getElementById("requests-tbody");
  const empty = document.getElementById("requests-empty");
  tbody.innerHTML = "";
  empty.style.display = items.length ? "none" : "block";

  items.forEach((r) => {
    const period = r.end_date
      ? `${formatDate(r.start_date)} — ${formatDate(r.end_date)}`
      : formatDate(r.start_date);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>№${r.id}</td>
      <td><a href="/admin/users/${r.user_id}">${escapeHtml(r.employee_name)}</a></td>
      <td>${escapeHtml(r.type_label)}</td>
      <td>${period}</td>
      <td><span class="badge ${statusBadgeClass(r.status)}">${escapeHtml(r.status_label)}</span></td>
      <td class="muted">${formatDate(r.created_at)}</td>
      <td class="text-right"><a class="btn btn-ghost btn-sm" href="/admin/requests/${r.id}">Открыть</a></td>
    `;
    tbody.appendChild(tr);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadRequests();
  document.getElementById("btn-filter").addEventListener("click", loadRequests);
  document.getElementById("f-only-open").addEventListener("change", loadRequests);
  document.getElementById("f-employee").addEventListener("keydown", (e) => {
    if (e.key === "Enter") loadRequests();
  });
});
