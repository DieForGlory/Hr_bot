// admin/static/admin.js
// Общий помощник для запросов к JSON API и всплывающих уведомлений.

async function apiFetch(url, options = {}) {
  const opts = Object.assign({}, options);
  opts.headers = Object.assign(
    { "X-Requested-With": "fetch" },
    options.headers || {}
  );
  if (options.json !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(options.json);
    delete opts.json;
  }

  const res = await fetch(url, opts);

  if (res.status === 401) {
    window.location.href = "/admin/login";
    throw new Error("not_authenticated");
  }

  let data = null;
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    data = await res.json();
  }

  if (!res.ok) {
    const message = (data && (data.detail || data.message)) || `Ошибка запроса (${res.status})`;
    const err = new Error(typeof message === "string" ? message : JSON.stringify(message));
    err.status = res.status;
    err.data = data;
    throw err;
  }

  return data;
}

function showToast(message, type = "success") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

function humanizeError(err) {
  return err && err.message ? err.message : "Что-то пошло не так";
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-confirm]").forEach((el) => {
    // capture:true + stopImmediatePropagation гарантирует, что при отмене
    // ни один другой обработчик click на этом же элементе не выполнится
    el.addEventListener("click", (e) => {
      if (!window.confirm(el.dataset.confirm)) {
        e.preventDefault();
        e.stopImmediatePropagation();
      }
    }, true);
  });
});
