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

// Sideways entrance effect for the course page.
document.addEventListener('scroll', function() {
    const slides = document.querySelectorAll('.course-slide');
    const windowHeight = window.innerHeight;
    const centerScreen = windowHeight / 2;

    slides.forEach(slide => {
      const rect = slide.getBoundingClientRect();
      const slideCenter = rect.top + rect.height / 2;
      const distanceFromCenter = Math.abs(centerScreen - slideCenter);
      
      if (rect.top < window.innerHeight && rect.bottom > 0) {
        slide.classList.add('visible');
        const opacity = Math.max(0, 1 - distanceFromCenter / centerScreen);
        slide.style.opacity = opacity;
      } else {
        slide.classList.remove('visible');
        slide.style.opacity = 1;
      }
    });
});
