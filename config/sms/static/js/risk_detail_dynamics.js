// Refresh page when coming back from action detail
// Check both event.persisted (bfcache) and sessionStorage flag for reliability
window.addEventListener('pageshow', function(event) {
    if (event.persisted || sessionStorage.getItem('refreshOnBack') === 'true') {
        sessionStorage.removeItem('refreshOnBack');
        window.location.reload();
    }
});