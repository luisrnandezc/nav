// Get data from Django template variables via data attributes
const pdfDataElement = document.getElementById('pdf-data');
const pdfUrl = pdfDataElement.getAttribute('data-pdf-url');

// Synthetic <a download> + programmatic .click() is not a user gesture on WebKit
// (iOS/iPadOS; all browsers there use WebKit) and often does nothing. Top-level
// navigation to the PDF URL does respect the server's Content-Disposition.
//
// Run auto-navigation at most once per evaluation so "Back" from the PDF viewer
// does not immediately trigger another download.
const autoKey = 'fms-pdf-auto:' + pdfUrl;
if (!sessionStorage.getItem(autoKey)) {
  sessionStorage.setItem(autoKey, '1');
  requestAnimationFrame(function () {
    window.location.assign(pdfUrl);
  });
}
