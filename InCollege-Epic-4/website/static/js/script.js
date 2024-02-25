// Inside website/static/js/script.js
document.addEventListener("DOMContentLoaded", function() {
    // Make submenu dropdowns clickable
    document.querySelectorAll('.dropdown-submenu a').forEach(function(element) {
      element.onclick = function(e) {
        e.stopPropagation();
        this.nextElementSibling.classList.toggle('show');
      };
    });
  });
  