document.addEventListener('DOMContentLoaded', function() {
    const loadMoreButtons = document.querySelectorAll('.load-more-btn');
    
    loadMoreButtons.forEach(button => {
        const flightList = button.previousElementSibling;
        const type = button.getAttribute('data-type');
        const role = button.getAttribute('data-role');
        const loadMoreUrl = button.getAttribute('data-url');
        
        // Count how many items are already displayed
        const existingItems = flightList.querySelectorAll('.flight-item, a.flight-item').length;
        let offset = existingItems;
        let isLoading = false;
        
        // Check if we should show the button initially
        checkIfMoreAvailable(button, type, role, offset, loadMoreUrl);
        
        button.addEventListener('click', function() {
            if (isLoading) return;
            
            isLoading = true;
            button.textContent = 'Cargando...';
            button.disabled = true;
            
            fetch(`${loadMoreUrl}?type=${type}&role=${role}&offset=${offset}&limit=20`)
                .then(response => response.json())
                .then(data => {
                    if (data.html) {
                        flightList.insertAdjacentHTML('beforeend', data.html);
                        offset += data.loaded_count;
                        
                        if (data.has_more) {
                            button.textContent = 'Cargar más';
                            button.disabled = false;
                            button.style.display = 'block';
                        } else {
                            button.style.display = 'none';
                        }
                    } else {
                        button.style.display = 'none';
                    }
                    isLoading = false;
                })
                .catch(error => {
                    console.error('Error loading more flights:', error);
                    button.textContent = 'Cargar más';
                    button.disabled = false;
                    isLoading = false;
                });
        });
    });
    
    function checkIfMoreAvailable(button, type, role, currentOffset, loadMoreUrl) {
        fetch(`${loadMoreUrl}?type=${type}&role=${role}&offset=${currentOffset}&limit=1`)
            .then(response => response.json())
            .then(data => {
                if (data.has_more) {
                    button.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error checking for more flights:', error);
            });
    }
});

