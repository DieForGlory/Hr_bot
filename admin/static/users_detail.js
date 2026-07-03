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
      };
      try {
        await apiFetch(`/api/admin/users/${USER_ID}`, { method: "PATCH", json: payload });
        showToast("Данные сохранены");
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
});
