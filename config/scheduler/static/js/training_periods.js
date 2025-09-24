// Training Periods JavaScript
// Handles clickable slots for flight request creation

document.addEventListener('DOMContentLoaded', function() {
    const clickableSlots = document.querySelectorAll('.clickable-slot');
    
    clickableSlots.forEach(slot => {
        slot.addEventListener('click', function() {
            const slotId = this.getAttribute('data-slot-id');
            const date = this.getAttribute('data-date');
            const block = this.getAttribute('data-block');
            const aircraft = this.getAttribute('data-aircraft');
            
            // Show confirmation dialog
            const confirmed = confirm(
                `¿Deseas reservar esta sesión?\n\n` +
                `Fecha: ${date}\n` +
                `Bloque: ${block}\n` +
                `Aeronave: ${aircraft}`
            );
            
            if (confirmed) {
                // Make the request
                fetch(`/scheduler/flight-request/create/${slotId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': window.csrfToken,
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Sesión reservada exitosamente');
                        // Reload the page to show updated status
                        window.location.reload();
                    } else {
                        alert('Error al reservar la sesión: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error al reservar la sesión:', error);
                    alert('Error al reservar la sesión');
                });
            }
        });
    });
});
