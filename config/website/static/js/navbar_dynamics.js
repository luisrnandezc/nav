// navbar burger animation
const burger = document.querySelector('.burger');
const navLinks = document.querySelector('.nav-links');

burger.addEventListener('click', () => {
    navLinks.classList.toggle('nav-active');
    burger.classList.toggle('toggle');
})

// navbar scrolling-hide effect.
document.addEventListener('DOMContentLoaded', () => {
    let lastScrollY = window.scrollY;
    const navbar = document.querySelector('.navbar'); // Navbar element

    window.addEventListener('scroll', () => {
        if (window.scrollY > lastScrollY) {
            // Scrolling down, hide navbar
            navbar.classList.add('hidden');
        } else {
            // Scrolling up, show navbar
            navbar.classList.remove('hidden');
        }
        lastScrollY = window.scrollY;
    });
});