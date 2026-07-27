(() => {
  const overlay = document.getElementById("confirm-modal-overlay");
  const messageEl = document.getElementById("confirm-modal-message");
  const cancelBtn = document.getElementById("confirm-modal-cancel");
  const confirmBtn = document.getElementById("confirm-modal-confirm");
  let pendingForm = null;

  function openConfirm(form, message) {
    pendingForm = form;
    messageEl.textContent = message;
    overlay.hidden = false;
  }

  function closeConfirm() {
    overlay.hidden = true;
    pendingForm = null;
  }

  cancelBtn.addEventListener("click", closeConfirm);
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closeConfirm();
  });

  confirmBtn.addEventListener("click", () => {
    const form = pendingForm;
    closeConfirm();
    if (form) form.submit();
  });

  document.addEventListener("submit", (e) => {
    const form = e.target;
    if (form.dataset.confirmMessage) {
      e.preventDefault();
      openConfirm(form, form.dataset.confirmMessage);
    }
  });
})();