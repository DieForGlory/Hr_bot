// admin/static/requests_detail.js

function openModal(id) { document.getElementById(id).classList.add("open"); }
function closeModal(id) { document.getElementById(id).classList.remove("open"); }

function reloadAfterDelay() {
  setTimeout(() => window.location.reload(), 500);
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-close-modal]").forEach((btn) => {
    btn.addEventListener("click", () => closeModal(btn.dataset.closeModal));
  });

  // Стадию "pending" (ждёт руководителя) HR решает только в Telegram — из веба доступна
  // лишь HR-стадия (manager_approved), см. admin/routers/requests.py.
  if (IS_VACATION && REQ_STATUS === "manager_approved") {
    document.getElementById("actions-vacation").style.display = "flex";
  } else if (IS_CERT && REQ_STATUS === "pending") {
    document.getElementById("actions-cert-pending").style.display = "flex";
  } else if (IS_CERT && REQ_STATUS === "in_progress") {
    document.getElementById("actions-cert-progress").style.display = "flex";
  }

  // --- Отпуск: согласовать ---
  const btnApprove = document.getElementById("btn-approve");
  if (btnApprove) btnApprove.addEventListener("click", () => openModal("modal-approve"));
  const modalApproveSubmit = document.getElementById("modal-approve-submit");
  if (modalApproveSubmit) {
    modalApproveSubmit.addEventListener("click", async () => {
      const comment = document.getElementById("approve-comment").value.trim();
      try {
        await apiFetch(`/api/admin/requests/${REQ_ID}/approve`, { method: "POST", json: { comment: comment || null } });
        showToast("Заявка согласована");
        closeModal("modal-approve");
        reloadAfterDelay();
      } catch (e) {
        showToast(humanizeError(e), "error");
      }
    });
  }

  // --- Отпуск: отклонить ---
  const btnReject = document.getElementById("btn-reject");
  if (btnReject) btnReject.addEventListener("click", () => openModal("modal-reject"));
  const modalRejectSubmit = document.getElementById("modal-reject-submit");
  if (modalRejectSubmit) {
    modalRejectSubmit.addEventListener("click", async () => {
      const comment = document.getElementById("reject-comment").value.trim();
      if (!comment) { showToast("Комментарий обязателен", "error"); return; }
      try {
        await apiFetch(`/api/admin/requests/${REQ_ID}/reject`, { method: "POST", json: { comment } });
        showToast("Заявка отклонена");
        closeModal("modal-reject");
        reloadAfterDelay();
      } catch (e) {
        showToast(humanizeError(e), "error");
      }
    });
  }

  // --- Справка: взять в работу ---
  const btnCertProgress = document.getElementById("btn-cert-progress");
  if (btnCertProgress) {
    btnCertProgress.addEventListener("click", async () => {
      try {
        await apiFetch(`/api/admin/requests/${REQ_ID}/cert-progress`, { method: "POST" });
        showToast("Взято в работу");
        reloadAfterDelay();
      } catch (e) {
        showToast(humanizeError(e), "error");
      }
    });
  }

  // --- Справка: готово ---
  [document.getElementById("btn-cert-done"), document.getElementById("btn-cert-done-2")].forEach((btn) => {
    if (btn) btn.addEventListener("click", () => openModal("modal-cert-done"));
  });
  const modalCertDoneSubmit = document.getElementById("modal-cert-done-submit");
  if (modalCertDoneSubmit) {
    modalCertDoneSubmit.addEventListener("click", async () => {
      const fileInput = document.getElementById("cert-done-file");
      const note = document.getElementById("cert-done-note").value.trim();
      const fd = new FormData();
      if (fileInput.files[0]) fd.append("file", fileInput.files[0]);
      if (note) fd.append("pickup_note", note);
      try {
        await apiFetch(`/api/admin/requests/${REQ_ID}/cert-done`, { method: "POST", body: fd });
        showToast("Сотрудник уведомлён о готовности справки");
        closeModal("modal-cert-done");
        reloadAfterDelay();
      } catch (e) {
        showToast(humanizeError(e), "error");
      }
    });
  }

  // --- Справка: отклонить ---
  [document.getElementById("btn-cert-reject"), document.getElementById("btn-cert-reject-2")].forEach((btn) => {
    if (btn) btn.addEventListener("click", () => openModal("modal-cert-reject"));
  });
  const modalCertRejectSubmit = document.getElementById("modal-cert-reject-submit");
  if (modalCertRejectSubmit) {
    modalCertRejectSubmit.addEventListener("click", async () => {
      const comment = document.getElementById("cert-reject-comment").value.trim();
      if (!comment) { showToast("Комментарий обязателен", "error"); return; }
      try {
        await apiFetch(`/api/admin/requests/${REQ_ID}/cert-reject`, { method: "POST", json: { comment } });
        showToast("Заявка отклонена");
        closeModal("modal-cert-reject");
        reloadAfterDelay();
      } catch (e) {
        showToast(humanizeError(e), "error");
      }
    });
  }
});
