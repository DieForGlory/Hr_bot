// admin/static/faq.js

document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("modal-faq");

  document.getElementById("btn-new-faq").addEventListener("click", () => {
    document.getElementById("modal-faq-title").textContent = "Новый вопрос";
    document.getElementById("faq-id").value = "";
    document.getElementById("faq-question").value = "";
    document.getElementById("faq-answer").value = "";
    modal.classList.add("open");
  });

  document.querySelectorAll("[data-edit-id]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.getElementById("modal-faq-title").textContent = "Изменить вопрос";
      document.getElementById("faq-id").value = btn.dataset.editId;
      document.getElementById("faq-question").value = btn.dataset.editQ;
      document.getElementById("faq-answer").value = btn.dataset.editA;
      modal.classList.add("open");
    });
  });

  document.querySelectorAll("[data-close-modal]").forEach((btn) => {
    btn.addEventListener("click", () => document.getElementById(btn.dataset.closeModal).classList.remove("open"));
  });

  document.querySelectorAll("[data-delete-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await apiFetch(`/api/admin/faq/${btn.dataset.deleteId}`, { method: "DELETE" });
        showToast("Вопрос удалён");
        setTimeout(() => window.location.reload(), 400);
      } catch (e) {
        showToast(humanizeError(e), "error");
      }
    });
  });

  document.getElementById("modal-faq-submit").addEventListener("click", async () => {
    const id = document.getElementById("faq-id").value;
    const question = document.getElementById("faq-question").value.trim();
    const answer = document.getElementById("faq-answer").value.trim();
    if (!question || !answer) { showToast("Заполните вопрос и ответ", "error"); return; }

    try {
      if (id) {
        await apiFetch(`/api/admin/faq/${id}`, { method: "PATCH", json: { question, answer } });
      } else {
        await apiFetch("/api/admin/faq", { method: "POST", json: { question, answer } });
      }
      showToast("Сохранено");
      modal.classList.remove("open");
      setTimeout(() => window.location.reload(), 400);
    } catch (e) {
      showToast(humanizeError(e), "error");
    }
  });
});
