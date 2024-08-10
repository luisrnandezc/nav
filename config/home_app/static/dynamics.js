const burger = document.querySelector('.burger-menu');
const navLinks = document.querySelector('.nav-item');

burger.addEventListener('click', () => {
    navLinks.classList.toggle('nav-active');

    // Burger Animation
    burger.classList.toggle('toggle');
})