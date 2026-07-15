// admin/static/users_detail.js

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("user-form");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const payload = {
        full_name: fd.get("full_name") || null,
        department: fd.get("department") || null,
        position: fd.get("position") || null,
        role: fd.get("role"),
        manager_id: fd.get("manager_id") ? parseInt(fd.get("manager_id"), 10) : null,
        vacation_days_balance: fd.get("vacation_days_balance") !== "" ? parseInt(fd.get("vacation_days_balance"), 10) : null,
        is_active: fd.get("is_active") === "on",
        hire_date: fd.get("hire_date") ? fd.get("hire_date").trim() : null,
        used_work_days: fd.get("used_work_days") !== "" ? parseFloat(fd.get("used_work_days")) : null,
        used_calendar_days: fd.get("used_calendar_days") !== "" ? parseFloat(fd.get("used_calendar_days")) : null,
        // пусто -> null: вернуть автоматический расчёт начисления от даты приёма
        accrued_work_override: fd.get("accrued_work_override") !== "" ? parseFloat(fd.get("accrued_work_override")) : null,
        accrued_calendar_override: fd.get("accrued_calendar_override") !== "" ? parseFloat(fd.get("accrued_calendar_override")) : null,
      };
      try {
        await apiFetch(`/api/admin/users/${USER_ID}`, { method: "PATCH", json: payload });
        showToast("Данные сохранены");
        setTimeout(() => window.location.reload(), 500);
      } catch (e) {
        showToast(humanizeError(e), "error");
      }
    });
  }

  // Блок «логин/пароль» удалён: доступ в админку теперь выдаёт auth-service (роли
  // сервиса hr_bot), а не эта форма.

  const approveBtn = document.getElementById("btn-approve-reg");
  if (approveBtn) {
    approveBtn.addEventListener("click", async () => {
      if (!window.confirm("Одобрить регистрацию сотрудника?")) return;
      try {
        await apiFetch(`/api/admin/users/${USER_ID}/approve`, { method: "POST" });
        showToast("Регистрация одобрена");
        setTimeout(() => window.location.reload(), 600);
      } catch (e) {
        showToast(humanizeError(e), "error");
      }
    });
  }

  const rejectBtn = document.getElementById("btn-reject-reg");
  if (rejectBtn) {
    rejectBtn.addEventListener("click", async () => {
      if (!window.confirm("Отклонить регистрацию сотрудника?")) return;
      try {
        await apiFetch(`/api/admin/users/${USER_ID}/reject`, { method: "POST" });
        showToast("Регистрация отклонена");
        setTimeout(() => window.location.reload(), 600);
      } catch (e) {
        showToast(humanizeError(e), "error");
      }
    });
  }

  const recalcBtn = document.getElementById("btn-recalc-manager");
  if (recalcBtn) {
    recalcBtn.addEventListener("click", async () => {
      try {
        const updated = await apiFetch(`/api/admin/users/${USER_ID}/recalculate-manager`, { method: "POST" });
        if (updated.manager_id) {
          showToast("Руководитель определён автоматически");
        } else {
          showToast("Руководитель этого уровня ещё не зарегистрирован — поле оставлено пустым", "error");
        }
        setTimeout(() => window.location.reload(), 800);
      } catch (e) {
        showToast(humanizeError(e), "error");
      }
    });
  }

  // --- Заявки сотрудника + опасная зона (п.6 ТЗ) ---
  const requestsBox = document.getElementById("user-requests");

  function fmtDate(iso) {
    if (!iso) return "-";
    const d = new Date(iso);
    return isNaN(d) ? iso : d.toLocaleDateString("ru-RU");
  }

  async function loadRequests() {
    if (!requestsBox) return;
    try {
      const data = await apiFetch(`/api/admin/requests?user_id=${USER_ID}`);
      const items = (data && data.items) || [];
      if (!items.length) {
        requestsBox.innerHTML = '<div class="muted">Заявок нет.</div>';
        return;
      }
      const rows = items.map((r) => `
        <tr>
          <td>#${r.id}</td>
          <td>${r.type_label || r.type}</td>
          <td>${r.status_label || r.status}</td>
          <td>${fmtDate(r.created_at)}</td>
          <td><button class="btn btn-sm btn-danger" data-del-req="${r.id}">Удалить</button></td>
        </tr>`).join("");
      requestsBox.innerHTML = `
        <table>
          <thead><tr><th>№</th><th>Тип</th><th>Статус</th><th>Подана</th><th></th></tr></thead>
          <tbody>${rows}</tbody>
        </table>`;
    } catch (e) {
      requestsBox.innerHTML = `<div class="muted">Не удалось загрузить: ${humanizeError(e)}</div>`;
    }
  }

  if (requestsBox) {
    requestsBox.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-del-req]");
      if (!btn) return;
      const reqId = btn.dataset.delReq;
      if (!window.confirm(`Удалить заявку #${reqId}? Действие необратимо.`)) return;
      try {
        await apiFetch(`/api/admin/requests/${reqId}`, { method: "DELETE" });
        showToast("Заявка удалена");
        loadRequests();
      } catch (err) {
        showToast(humanizeError(err), "error");
      }
    });
    loadRequests();
  }

  const clearHistoryBtn = document.getElementById("btn-clear-history");
  if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener("click", async () => {
      if (!window.confirm("Удалить ВСЕ заявки сотрудника? Действие необратимо.")) return;
      try {
        const res = await apiFetch(`/api/admin/users/${USER_ID}/requests`, { method: "DELETE" });
        showToast(`История очищена (удалено заявок: ${res.deleted})`);
        loadRequests();
      } catch (e) {
        showToast(humanizeError(e), "error");
      }
    });
  }

  const deleteUserBtn = document.getElementById("btn-delete-user");
  if (deleteUserBtn) {
    deleteUserBtn.addEventListener("click", async () => {
      if (!window.confirm("Удалить пользователя вместе со всеми его заявками? Действие необратимо.")) return;
      try {
        await apiFetch(`/api/admin/users/${USER_ID}`, { method: "DELETE" });
        showToast("Пользователь удалён");
        const base = window.BASE_PATH || "";
        setTimeout(() => { window.location.href = `${base}/admin/users`; }, 700);
      } catch (e) {
        showToast(humanizeError(e), "error");
      }
    });
  }
});
