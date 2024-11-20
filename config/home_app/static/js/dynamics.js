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
        // scroll down
        navbar.classList.add('hidden');
    } else {
        // scroll up
        navbar.classList.remove('hidden');
    }
    
    lastScrollTop = currentScroll <= 0 ? 0 : currentScroll; // for Mobile or negative scrolling
});

// 3) fade-in Side-in effect for the course page.
const scrollElements = document.querySelectorAll(".course-img,.course-info,.about-p");

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

// 5) slideshow for the about page.

let slideIndex = 1;
showSlides(slideIndex);

// next/previous controls
function plusSlides(n) {
  showSlides(slideIndex += n);
}

// thumbnail image controls
function currentSlide(n) {
  showSlides(slideIndex = n);
}

function showSlides(n) {
  let i;
  let slides = document.getElementsByClassName("slides");
  let dots = document.getElementsByClassName("dot");
  if (n > slides.length) {slideIndex = 1}
  if (n < 1) {slideIndex = slides.length}
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";
  }
  for (i = 0; i < dots.length; i++) {
    dots[i].className = dots[i].className.replace(" active", "");
  }
  slides[slideIndex-1].style.display = "block";
  dots[slideIndex-1].className += " active";
} 