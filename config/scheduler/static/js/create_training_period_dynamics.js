// Training Period Form Dynamic Behavior
// Handles date field interactions and period duration calculation

document.addEventListener('DOMContentLoaded', function() {
    const startDateField = document.getElementById('id_start_date');
    const endDateField = document.getElementById('id_end_date');

    if (!startDateField || !endDateField) {
        return; // Exit if fields don't exist
    }

    // Update end_date minimum when start_date changes
    startDateField.addEventListener('change', function() {
        const startDate = this.value;
        if (startDate) {
            endDateField.min = startDate;
            updatePeriodDuration();
        }
    });

    // Calculate and display period duration
    endDateField.addEventListener('change', updatePeriodDuration);

    function updatePeriodDuration() {
        const startDate = startDateField.value;
        const endDate = endDateField.value;
        const durationDisplay = document.getElementById('period-duration');
        
        if (startDate && endDate) {
            const start = new Date(startDate);
            const end = new Date(endDate);
            const diffTime = Math.abs(end - start);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
            
            // Update duration display
            durationDisplay.textContent = `${diffDays} días`;
        } else {
            // Show 0 days if either date is missing
            durationDisplay.textContent = '0 días';
        }
    }

    // Initial setup - set minimum date for end field if start date is already set
    if (startDateField.value) {
        endDateField.min = startDateField.value;
        updatePeriodDuration();
    }
});
