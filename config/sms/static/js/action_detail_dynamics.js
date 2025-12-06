function goBack() {
    // Set flag to refresh the page we're going back to
    // This is more reliable than relying on event.persisted
    sessionStorage.setItem('refreshOnBack', 'true');
    
    if (window.history.length > 1) {
        window.history.back();
    } else {
        // Fallback to SMS dashboard if no history
        window.location.href = window.location.origin + '/sms/';
    }
}