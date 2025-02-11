// navbar burger animation
const burger = document.querySelector('.burger');
const navLinks = document.querySelector('.nav-links');

burger.addEventListener('click', () => {
    navLinks.classList.toggle('nav-active');
    burger.classList.toggle('toggle');
})

// navbar scrolling-hide effect.
let lastScrollTop = 0;
const navbar = document.getElementById('navbar');

window.addEventListener('scroll', () => {
    let currentScroll = window.scrollY || document.documentElement.scrollTop;
    
    if (currentScroll > lastScrollTop) {
        // scroll down
        navbar.classList.add('hidden');
    } else {
        // scroll up
        navbar.classList.remove('hidden');
    }
    
    lastScrollTop = currentScroll <= 0 ? 0 : currentScroll; // for Mobile or negative scrolling
});