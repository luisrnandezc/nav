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
            
            // Show custom confirmation modal instead of browser confirm
            showFlightRequestConfirmation(slotId, date, block, aircraft, this);
        });
    });
    
    // ============================================================================
    // CUSTOM CONFIRMATION MODAL FUNCTIONS
    // ============================================================================
    
    function showFlightRequestConfirmation(slotId, date, block, aircraft, slotElement) {
        const modal = createConfirmationModal(slotId, date, block, aircraft, slotElement);
        document.body.appendChild(modal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    function createConfirmationModal(slotId, date, block, aircraft, slotElement) {
        const modal = document.createElement('div');
        modal.className = 'flight-request-modal';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'flight-request-modal-content';
        
        // Add title
        const title = document.createElement('h3');
        title.className = 'flight-request-modal-title';
        title.textContent = 'Confirmar Reserva de Sesión';
        modalContent.appendChild(title);
        
        // Add slot information
        const infoDiv = document.createElement('div');
        infoDiv.className = 'flight-request-info';
        infoDiv.innerHTML = `
            <div class="info-item">
                <strong>Fecha:</strong> ${date}
            </div>
            <div class="info-item">
                <strong>Bloque:</strong> ${block}
            </div>
            <div class="info-item">
                <strong>Aeronave:</strong> ${aircraft}
            </div>
        `;
        modalContent.appendChild(infoDiv);
        
        // Add confirmation question
        const questionDiv = document.createElement('div');
        questionDiv.className = 'flight-request-question';
        questionDiv.textContent = '¿Deseas reservar esta sesión?';
        modalContent.appendChild(questionDiv);
        
        // Add action buttons
        const buttonsContainer = document.createElement('div');
        buttonsContainer.className = 'flight-request-buttons';
        
        // Confirm button
        const confirmButton = document.createElement('button');
        confirmButton.textContent = 'Sí, Reservar';
        confirmButton.className = 'flight-request-confirm';
        confirmButton.addEventListener('click', () => {
            modal.remove();
            createFlightRequest(slotId, slotElement);
        });
        buttonsContainer.appendChild(confirmButton);
        
        // Cancel button
        const cancelButton = document.createElement('button');
        cancelButton.textContent = 'Cancelar';
        cancelButton.className = 'flight-request-cancel';
        cancelButton.addEventListener('click', () => {
            modal.remove();
        });
        buttonsContainer.appendChild(cancelButton);
        
        modalContent.appendChild(buttonsContainer);
        modal.appendChild(modalContent);
        return modal;
    }
    
    function createFlightRequest(slotId, slotElement) {
        // Show loading state
        const originalText = slotElement.textContent;
        slotElement.textContent = 'Procesando...';
        slotElement.style.pointerEvents = 'none';
        
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
                showSuccessNotification('Sesión reservada exitosamente');
                // Reload the page to show updated status
                setTimeout(() => window.location.reload(), 1500);
            } else {
                showErrorNotification('Error al reservar la sesión: ' + data.error);
                // Restore button state
                slotElement.textContent = originalText;
                slotElement.style.pointerEvents = 'auto';
            }
        })
        .catch(error => {
            console.error('Error al reservar la sesión:', error);
            showErrorNotification('Error al reservar la sesión');
            // Restore button state
            slotElement.textContent = originalText;
            slotElement.style.pointerEvents = 'auto';
        });
    }
    
    // ============================================================================
    // NOTIFICATION FUNCTIONS
    // ============================================================================
    
    function showSuccessNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'success-notification';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    function showErrorNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'error-notification';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Auto-remove after 8 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 8000);
    }
});
