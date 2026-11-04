(function () {
    try {
      var th = localStorage.getItem("input-from-web-theme") || "auto";
      var root = document.documentElement;
      if (th === "dark") { root.setAttribute("data-theme", "dark"); root.style.colorScheme = "dark"; }
      else if (th === "light") { root.setAttribute("data-theme", "light"); root.style.colorScheme = "light"; }
      else { root.style.colorScheme = "light dark"; }
    } catch (e) {}
  })();
