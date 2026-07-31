(() => {
  const overlay = document.getElementById("delete-confirm-overlay");
  if (!overlay) return;

  const usernameLabel = document.getElementById("delete-confirm-username");
  const input = document.getElementById("delete-confirm-input");
  const cancelBtn = document.getElementById("delete-confirm-cancel");
  const submitBtn = document.getElementById("delete-confirm-submit");
  let pendingForm = null;
  let expectedUsername = "";

  function open(form, username) {
    pendingForm = form;
    expectedUsername = username;
    usernameLabel.textContent = username;
    input.value = "";
    submitBtn.disabled = true;
    overlay.hidden = false;
    input.focus();
  }

  function close() {
    overlay.hidden = true;
    pendingForm = null;
  }

  input.addEventListener("input", () => {
    submitBtn.disabled = input.value !== expectedUsername;
  });

  cancelBtn.addEventListener("click", close);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) close(); });

  submitBtn.addEventListener("click", () => {
    const form = pendingForm;
    close();
    if (form) form.submit();
  });

  document.addEventListener("submit", (e) => {
    const form = e.target;
    if (form.dataset.deleteUsername) {
      e.preventDefault();
      open(form, form.dataset.deleteUsername);
    }
  });
})();