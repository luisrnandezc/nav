// lateral movement effect for the about page.
let scrollPosition = 0;
let lastScrollY = 0;
let momentumOffset = 0;
let velocity = 0;
let isScrolling = false;

document.addEventListener("scroll", function() {
    scrollPosition = window.scrollY;
    isScrolling = true;
});

// function to update background positions
function updateBackgrounds() {
    document.querySelectorAll(".about-content").forEach((element, index) => {
        const direction = index % 2 === 0 ? 1 : -1;

        // additional offset for the first div (move it slightly to the left)
        const extraOffset = index === 0 ? -75 : 0; // adjust the first background 50px to the left

        // apply the momentum offset with direction and additional offset
        const horizontalMovement = (momentumOffset + (scrollPosition - lastScrollY) * 0.1 + extraOffset) * direction;
        
        element.style.backgroundPosition = `${horizontalMovement}px center`;
    });
}

// smooth deceleration effect
function smoothScrollEffect() {
    if (isScrolling) {
        // calculate the velocity based on the scroll delta
        velocity = (scrollPosition - lastScrollY) * 0.1;
        momentumOffset += velocity; // update momentum offset with current velocity
        lastScrollY = scrollPosition; // update last scroll position
        updateBackgrounds();
        isScrolling = false;
    } else {
        // gradually decrease velocity when scrolling stops
        velocity *= 0.985; // deceleration factor, adjust for a slower or faster stop
        momentumOffset += velocity; // update momentumOffset based on decelerated velocity
        updateBackgrounds();

        if (Math.abs(velocity) < 0.01) {
            velocity = 0; // stop completely when velocity is very low
        }
    }
    requestAnimationFrame(smoothScrollEffect);
}

// start the animation loop
smoothScrollEffect();

// Fade in effect for the about paragraph.
document.addEventListener("DOMContentLoaded", function () {
    const paragraphs = document.querySelectorAll(".fadein-p");

    if (!paragraphs) {
        console.error("Element with class 'about-p' not found!");
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("show");
                observer.unobserve(entry.target); // Stop observing after animation
            }
        });
    }, { threshold: 0.1 });

    paragraphs.forEach((paragraph) => observer.observe(paragraph));
});

// Carrusel effect activation.
const swiper = new Swiper('.swiper', {
    // Optional parameters
    direction: 'horizontal',
    loop: true,
  
    // If we need pagination
    pagination: {
      el: '.swiper-pagination',
    },
  
    // Navigation arrows
    navigation: {
      nextEl: '.swiper-button-next',
      prevEl: '.swiper-button-prev',
    },
});

// Right to left fadein effect for the blurry box.

// Detect when the div comes into view
const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if (entry.isIntersecting) {
            entry.target.classList.add("show");
        }
    });
});

// Select all elements to animate
document.querySelectorAll(".hidden").forEach((el) => observer.observe(el));