(() => {
  const form = document.getElementById("navbar-search-form");
  const input = document.getElementById("navbar-search-input");
  const tooltip = document.getElementById("navbar-search-tooltip");
  if (!form || !input || !tooltip) return;

  let hideTimer = null;

  form.addEventListener("submit", (e) => {
    if (!input.value.trim()) {
      e.preventDefault();
      tooltip.hidden = false;
      clearTimeout(hideTimer);
      hideTimer = setTimeout(() => { tooltip.hidden = true; }, 2000);
    }
  });

  input.addEventListener("input", () => {
    tooltip.hidden = true;
  });
})();