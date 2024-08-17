const burger = document.querySelector('.burger');
const navLinks = document.querySelector('.nav-links');

burger.addEventListener('click', () => {
    navLinks.classList.toggle('nav-active');

    // Burger Animation
    burger.classList.toggle('toggle');
})

// Navbar scrolling-hide effect.
let lastScrollTop = 0;
const navbar = document.getElementById('navbar');

window.addEventListener('scroll', () => {
    let currentScroll = window.scrollY || document.documentElement.scrollTop;
    
    if (currentScroll > lastScrollTop) {
        // Scroll down
        navbar.classList.add('hidden');
    } else {
        // Scroll up
        navbar.classList.remove('hidden');
    }
    
    lastScrollTop = currentScroll <= 0 ? 0 : currentScroll; // For Mobile or negative scrolling
});
