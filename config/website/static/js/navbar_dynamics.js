// navbar burger animation
const burger = document.querySelector('.burger');
const navLinks = document.querySelector('.nav-links');

burger.addEventListener('click', () => {
    navLinks.classList.toggle('nav-active');
    burger.classList.toggle('toggle');
})

// navbar scrolling-hide effect.
document.addEventListener('DOMContentLoaded', () => {
    let navbarLastScrollY = window.scrollY;
    const navbar = document.querySelector('.navbar');

    window.addEventListener('scroll', () => {
        if (window.scrollY > navbarLastScrollY) {
            // Scrolling down, hide navbar
            navbar.classList.add('navbar-hidden');
        } else {
            // Scrolling up, show navbar
            navbar.classList.remove('navbar-hidden');
        }
        navbarLastScrollY = window.scrollY;
    });
});