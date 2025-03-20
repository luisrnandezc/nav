document.addEventListener("DOMContentLoaded", function() {
    const boxes = document.querySelectorAll(".course-box");

    const box_observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
            }
        });
    }, { threshold: 0.2});

    boxes.forEach(box => box_observer.observe(box));
});