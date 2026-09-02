document.addEventListener("DOMContentLoaded", function () {
  const accountButton = document.getElementById("accountButton");
  const accountMenu = document.getElementById("accountMenu");

  if (!accountButton || !accountMenu) {
    return;
  }

  accountButton.addEventListener("click", function (event) {
    event.stopPropagation();

    const isOpen = !accountMenu.hasAttribute("hidden");

    if (isOpen) {
      accountMenu.setAttribute("hidden", "");
      accountButton.setAttribute("aria-expanded", "false");
    } else {
      accountMenu.removeAttribute("hidden");
      accountButton.setAttribute("aria-expanded", "true");
    }
  });

  document.addEventListener("click", function (event) {
    if (
      !accountMenu.contains(event.target) &&
      !accountButton.contains(event.target)
    ) {
      accountMenu.setAttribute("hidden", "");
      accountButton.setAttribute("aria-expanded", "false");
    }
  });
});
