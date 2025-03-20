document.addEventListener('DOMContentLoaded', () => {
    // navbar burger animation
    const burger = document.querySelector('.burger');
    const navLinks = document.querySelector('.nav-links');
    const navbar = document.querySelector('.navbar');

    if (burger && navLinks) {
        burger.addEventListener('click', () => {
            navLinks.classList.toggle('nav-active');
            burger.classList.toggle('toggle');
        });
    }

    // navbar scrolling-hide effect.
    if (navbar) {
        let navbarLastScrollY = window.scrollY;
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
    }
});