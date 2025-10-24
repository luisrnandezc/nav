document.addEventListener('DOMContentLoaded', function() {
    let currentOffset = 90; // Start from 90 since we loaded 90 initially
    const loadMoreBtn = document.getElementById('load-more-flights');
    const loadingIndicator = document.getElementById('loading-indicator');
    const tbody = document.getElementById('flight-logs-tbody');
    
    // Get the URL from a data attribute on the body or a script tag
    const loadMoreUrl = document.body.getAttribute('data-load-more-url') || '/fms/api/load_more_flights/';
    
    // Check if we should show the load more button initially
    checkIfMoreFlightsAvailable();
    
    loadMoreBtn.addEventListener('click', function() {
        loadMoreFlights();
    });
    
    function checkIfMoreFlightsAvailable() {
        // Make a quick request to check if there are more flights
        fetch(`${loadMoreUrl}?offset=${currentOffset}&limit=1`)
            .then(response => response.json())
            .then(data => {
                if (data.has_more) {
                    loadMoreBtn.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error checking for more flights:', error);
            });
    }
    
    function loadMoreFlights() {
        loadMoreBtn.style.display = 'none';
        loadingIndicator.style.display = 'block';
        
        fetch(`${loadMoreUrl}?offset=${currentOffset}&limit=30`)
            .then(response => response.json())
            .then(data => {
                // Append new rows to the table
                tbody.insertAdjacentHTML('beforeend', data.html);
                
                // Update offset
                currentOffset += data.loaded_count;
                
                // Hide loading indicator
                loadingIndicator.style.display = 'none';
                
                // Show load more button if there are more flights
                if (data.has_more) {
                    loadMoreBtn.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error loading more flights:', error);
                loadingIndicator.style.display = 'none';
                loadMoreBtn.style.display = 'block';
            });
    }
});
