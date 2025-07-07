// Get data from Django template variables via data attributes
const pdfDataElement = document.getElementById('pdf-data');
const pdfUrl = pdfDataElement.getAttribute('data-pdf-url');
const filename = pdfDataElement.getAttribute('data-filename');
const dashboardUrl = pdfDataElement.getAttribute('data-dashboard-url');

// Trigger PDF download
const link = document.createElement('a');
link.href = pdfUrl;
link.download = filename;
document.body.appendChild(link);
link.click();
document.body.removeChild(link);

// Countdown and redirect
let countdown = 3;
const countdownElement = document.getElementById('countdown');

const timer = setInterval(function() {
    countdown--;
    countdownElement.textContent = countdown;
    
    if (countdown <= 0) {
        clearInterval(timer);
        window.location.href = dashboardUrl;
    }
}, 1000);