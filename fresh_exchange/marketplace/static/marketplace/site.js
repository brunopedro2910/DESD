document.querySelectorAll('.flash button').forEach(function (button) {
  button.addEventListener('click', function () { button.parentElement.remove(); });
});

var menuButton = document.querySelector('.menu-button');
var mobileMenu = document.querySelector('.mobile-menu');
if (menuButton && mobileMenu) {
  menuButton.addEventListener('click', function () { mobileMenu.classList.toggle('open'); });
}
