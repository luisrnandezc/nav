document.addEventListener('DOMContentLoaded', () => {
    // Fetch course start date
    fetch('course-date.json')
        .then(response => response.json())
        .then(data => {
            const startDateElement = document.getElementById('start-date');
            if (startDateElement) {
                startDateElement.textContent = data.start_date;
            }
        })
        .catch(error => {
            console.error('Error fetching course date:', error);
        });

    // WhatsApp link handlers - handles buttons/links with data-whatsapp attribute
    const whatsappLinks = document.querySelectorAll('[data-whatsapp]');
    whatsappLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const phoneNumber = link.getAttribute('data-whatsapp');
            window.open(`https://wa.me/${phoneNumber}`, '_blank');
        });
    });
});