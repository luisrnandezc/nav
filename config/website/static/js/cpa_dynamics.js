document.addEventListener('DOMContentLoaded', () => {
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