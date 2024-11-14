// 1) navbar burger animation
const burger = document.querySelector('.burger');
const navLinks = document.querySelector('.nav-links');

burger.addEventListener('click', () => {
    navLinks.classList.toggle('nav-active');
    burger.classList.toggle('toggle');
})

// 2) navbar scrolling-hide effect.
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

// 3) fade-in Side-in effect for the course page.
const scrollElements = document.querySelectorAll(".course-img,.course-info");

const elementInView = (el, dividend = 1) => {
  const elementTop = el.getBoundingClientRect().top;

  return (
    elementTop <=
    (window.innerHeight || document.documentElement.clientHeight) / dividend
  );
};

const elementOutofView = (el) => {
  const elementTop = el.getBoundingClientRect().top;

  return (
    elementTop > (window.innerHeight || document.documentElement.clientHeight)
  );
};

const displayScrollElement = (element) => {
  element.classList.add("scrolled");
};

const hideScrollElement = (element) => {
  element.classList.remove("scrolled");
};

const handleScrollAnimation = () => {
  scrollElements.forEach((el) => {
    if (elementInView(el, 1.05)) {
      displayScrollElement(el);
    } else if (elementOutofView(el)) {
      hideScrollElement(el)
    }
  })
}

window.addEventListener("scroll", () => { 
  handleScrollAnimation();
});

// 4) lateral movement effect for the about page.
let scrollPosition = 0;
let lastScrollY = 0;
let momentumOffset = 0;
let velocity = 0;
let isScrolling = false;

document.addEventListener("scroll", function() {
    scrollPosition = window.scrollY;
    isScrolling = true;
});

// Function to update background positions
function updateBackgrounds() {
    document.querySelectorAll(".about-content").forEach((element, index) => {
        const direction = index % 2 === 0 ? 1 : -1;

        // Additional offset for the first div (move it slightly to the left)
        const extraOffset = index === 0 ? -75 : 0; // Adjust the first background 50px to the left

        // Apply the momentum offset with direction and additional offset
        const horizontalMovement = (momentumOffset + (scrollPosition - lastScrollY) * 0.1 + extraOffset) * direction;
        
        element.style.backgroundPosition = `${horizontalMovement}px center`;
    });
}

// Smooth deceleration effect
function smoothScrollEffect() {
    if (isScrolling) {
        // Calculate the velocity based on the scroll delta
        velocity = (scrollPosition - lastScrollY) * 0.1;
        momentumOffset += velocity; // Update momentum offset with current velocity
        lastScrollY = scrollPosition; // Update last scroll position
        updateBackgrounds();
        isScrolling = false;
    } else {
        // Gradually decrease velocity when scrolling stops
        velocity *= 0.985; // Deceleration factor, adjust for a slower or faster stop
        momentumOffset += velocity; // Update momentumOffset based on decelerated velocity
        updateBackgrounds();

        if (Math.abs(velocity) < 0.01) {
            velocity = 0; // Stop completely when velocity is very low
        }
    }
    requestAnimationFrame(smoothScrollEffect);
}

// Start the animation loop
smoothScrollEffect();