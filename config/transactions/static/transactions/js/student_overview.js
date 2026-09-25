// Keep one accessible copy of each movement's details across screen sizes.
// Without JavaScript, the server-rendered details remain open and readable.
const portraitMobile = window.matchMedia('(max-width: 768px) and (orientation: portrait)');

function updateMovementDetails() {
    document.querySelectorAll('.movement-details').forEach(details => {
        details.open = !portraitMobile.matches;
    });
}

updateMovementDetails();
portraitMobile.addEventListener('change', updateMovementDetails);
