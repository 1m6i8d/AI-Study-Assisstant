(() => {
  function applySticky() {
    const navbar = document.querySelector(".admin-navbar");
    const navHeight = navbar ? navbar.getBoundingClientRect().height : 0;
    document.documentElement.style.setProperty("--admin-sticky-offset", navHeight + "px");
  }

  window.addEventListener("load", applySticky);
  window.addEventListener("resize", applySticky);
})();