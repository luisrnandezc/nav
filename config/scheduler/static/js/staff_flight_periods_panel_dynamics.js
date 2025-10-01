// Staff Periods Panel JavaScript
// Handles clickable slots for staff to change slot status and period activation

document.addEventListener('DOMContentLoaded', function() {
    // Handle slot status changes
    const staffClickableSlots = document.querySelectorAll('.staff-clickable-slot');
    
    staffClickableSlots.forEach(slot => {
        slot.addEventListener('click', function() {
            const slotId = this.getAttribute('data-slot-id');
            const date = this.getAttribute('data-date');
            const block = this.getAttribute('data-block');
            const aircraft = this.getAttribute('data-aircraft');
            const currentStatus = this.getAttribute('data-current-status');
            
            // Determine the action based on current status
            let action, newStatus, confirmationMessage;
            
            if (currentStatus === 'available') {
                action = 'unavailable';
                newStatus = 'unavailable';
                confirmationMessage = `¿Desea marcar esta sesión como NO DISPONIBLE?\n\n` +
                    `Fecha: ${date}\n` +
                    `Bloque: ${block}\n` +
                    `Aeronave: ${aircraft}`;
            } else if (currentStatus === 'unavailable') {
                action = 'available';
                newStatus = 'available';
                confirmationMessage = `¿Desea marcar esta sesión como DISPONIBLE?\n\n` +
                    `Fecha: ${date}\n` +
                    `Bloque: ${block}\n` +
                    `Aeronave: ${aircraft}`;
            } else if (currentStatus === 'reserved') {
                action = 'cancel_and_unavailable';
                newStatus = 'unavailable';
                confirmationMessage = `¿Desea cancelar la solicitud de vuelo y marcar esta sesión como NO DISPONIBLE?\n\n` +
                    `Fecha: ${date}\n` +
                    `Bloque: ${block}\n` +
                    `Aeronave: ${aircraft}\n\n` +
                    `Esto cancelará la solicitud de vuelo existente.`;
            } else {
                // For any other status, make it available
                action = 'available';
                newStatus = 'available';
                confirmationMessage = `¿Desea marcar esta sesión como DISPONIBLE?\n\n` +
                    `Fecha: ${date}\n` +
                    `Bloque: ${block}\n` +
                    `Aeronave: ${aircraft}`;
            }
            
            // Show confirmation dialog
            const confirmed = confirm(confirmationMessage);
            
            if (confirmed) {
                // Show loading state
                const button = this;
                const originalText = button.textContent;
                button.textContent = 'Procesando...';
                button.disabled = true;
                
                // Make the request
                fetch(`/scheduler/slot/change-status/${slotId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': window.csrfToken,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        action: action,
                        new_status: newStatus
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        let successMessage = '';
                        if (action === 'available') {
                            successMessage = 'Sesión marcada como DISPONIBLE';
                        } else if (action === 'unavailable') {
                            successMessage = 'Sesión marcada como NO DISPONIBLE';
                        } else if (action === 'cancel_and_unavailable') {
                            successMessage = 'Solicitud cancelada y sesión marcada como NO DISPONIBLE';
                        }
                        alert(successMessage);
                        // Reload the page to show updated status
                        window.location.reload();
                    } else {
                        alert('Error al cambiar el estado de la sesión: ' + data.error);
                        // Restore button state
                        button.textContent = originalText;
                        button.disabled = false;
                    }
                })
                .catch(error => {
                    console.error('Error al cambiar el estado de la sesión:', error);
                    alert('Error al cambiar el estado de la sesión');
                    // Restore button state
                    button.textContent = originalText;
                    button.disabled = false;
                });
            }
        });
    });

    // Handle period activation
    const activatePeriodButtons = document.querySelectorAll('.activate-period-button');
    
    activatePeriodButtons.forEach(button => {
        button.addEventListener('click', function() {
            const periodId = this.getAttribute('data-period-id');
            const aircraft = this.getAttribute('data-aircraft');
            
            // Show confirmation dialog
            const confirmed = confirm(
                `¿Deseas activar este período de entrenamiento?\n\n` +
                `Aeronave: ${aircraft}\n\n` +
                `Esto activará el período y lo hará disponible para solicitudes de vuelo.`
            );
            
            if (confirmed) {
                // Show loading state
                const originalText = this.textContent;
                this.textContent = 'Procesando...';
                this.disabled = true;
                
                // Make the request
                fetch(`/scheduler/period/activate/${periodId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': window.csrfToken,
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Período activado exitosamente');
                        // Reload the page to show updated status
                        window.location.reload();
                    } else {
                        alert('Error al activar el período: ' + data.error);
                        // Restore button state
                        this.textContent = originalText;
                        this.disabled = false;
                    }
                })
                .catch(error => {
                    console.error('Error al activar el período:', error);
                    alert('Error al activar el período');
                    // Restore button state
                    this.textContent = originalText;
                    this.disabled = false;
                });
            }
        });
    });
});
