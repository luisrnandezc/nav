// Staff Periods Panel JavaScript
// Handles clickable slots for staff to change slot status and assign instructors

document.addEventListener('DOMContentLoaded', function() {
    let contextMenu = null;
    let availableInstructors = [];
    
    // Initialize the application
    loadAvailableInstructors();
    setupSlotEventListeners();
    setupPeriodActivationListeners();
    
    // ============================================================================
    // INITIALIZATION FUNCTIONS
    // ============================================================================
    
    function loadAvailableInstructors() {
        fetch('/scheduler/instructors/available/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': window.csrfToken,
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                availableInstructors = data.instructors;
            }
        })
        .catch(error => {
            console.error('Error loading instructors:', error);
        });
    }
    
    function setupSlotEventListeners() {
        const staffClickableSlots = document.querySelectorAll('.staff-clickable-slot');
        
        staffClickableSlots.forEach(slot => {
            slot.addEventListener('contextmenu', function(e) {
                e.preventDefault();
                showContextMenu(e, this);
            });
            
            // Also handle left-click for backward compatibility (show context menu)
            slot.addEventListener('click', function(e) {
                e.preventDefault();
                showContextMenu(e, this);
            });
        });
    }
    
    function setupPeriodActivationListeners() {
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
                    activatePeriod(periodId, this);
                }
            });
        });
    }
    
    // ============================================================================
    // CONTEXT MENU FUNCTIONS
    // ============================================================================
    
    function showContextMenu(event, slotElement) {
        // Remove existing context menu
        if (contextMenu) {
            contextMenu.remove();
        }
        
        const slotData = extractSlotData(slotElement);
        
        // Create context menu
        contextMenu = createContextMenuElement(event, slotData);
        document.body.appendChild(contextMenu);
        
        // Close context menu when clicking outside
        setTimeout(() => {
            document.addEventListener('click', closeContextMenu);
        }, 100);
    }
    
    function extractSlotData(slotElement) {
        return {
            slotId: slotElement.getAttribute('data-slot-id'),
            date: slotElement.getAttribute('data-date'),
            block: slotElement.getAttribute('data-block'),
            aircraft: slotElement.getAttribute('data-aircraft'),
            currentStatus: slotElement.getAttribute('data-current-status'),
            hasInstructor: slotElement.getAttribute('data-has-instructor') === 'true',
            instructorName: slotElement.getAttribute('data-instructor-name'),
            element: slotElement
        };
    }
    
    function createContextMenuElement(event, slotData) {
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.style.top = `${event.clientY}px`;
        menu.style.left = `${event.clientX}px`;
        
        // Add slot info header
        const header = document.createElement('div');
        header.className = 'context-menu-header';
        header.textContent = `${slotData.aircraft} - ${slotData.date} - ${slotData.block}`;
        menu.appendChild(header);
        
        // Add action buttons
        const actionsContainer = document.createElement('div');
        actionsContainer.className = 'context-menu-actions';
        
        addStatusChangeActions(actionsContainer, slotData);
        addInstructorActions(actionsContainer, slotData);
        
        menu.appendChild(actionsContainer);
        return menu;
    }
    
    function addStatusChangeActions(container, slotData) {
        const { currentStatus, slotId, element } = slotData;
        
        if (currentStatus === 'available') {
            addActionButton(container, 'Marcar como No Disponible', () => {
                changeSlotStatus(slotId, 'unavailable', 'unavailable', element);
            });
        } else if (currentStatus === 'unavailable') {
            addActionButton(container, 'Marcar como Disponible', () => {
                changeSlotStatus(slotId, 'available', 'available', element);
            });
        } else if (currentStatus === 'reserved' || currentStatus === 'pending') {
            addActionButton(container, 'Cancelar y Marcar No Disponible', () => {
                changeSlotStatus(slotId, 'cancel_and_unavailable', 'unavailable', element);
            });
        }
    }
    
    function addInstructorActions(container, slotData) {
        const { hasInstructor, instructorName, slotId, element } = slotData;
        
        if (hasInstructor) {
            addActionButton(container, `Remover Instructor (${instructorName})`, () => {
                assignInstructor(slotId, 'remove', null, element);
            });
        } else {
            addActionButton(container, 'Asignar Instructor', () => {
                showInstructorSelector(slotId, element);
            });
        }
    }
    
    function addActionButton(container, text, onClick) {
        const button = document.createElement('button');
        button.textContent = text;
        button.className = 'context-menu-button';
        button.addEventListener('click', () => {
            onClick();
            closeContextMenu();
        });
        container.appendChild(button);
    }
    
    function closeContextMenu() {
        if (contextMenu) {
            contextMenu.remove();
            contextMenu = null;
        }
        document.removeEventListener('click', closeContextMenu);
    }
    
    // ============================================================================
    // INSTRUCTOR SELECTION FUNCTIONS
    // ============================================================================
    
    function showInstructorSelector(slotId, slotElement) {
        if (availableInstructors.length === 0) {
            alert('No hay instructores disponibles');
            return;
        }
        
        const modal = createInstructorModal(slotId, slotElement);
        document.body.appendChild(modal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    function createInstructorModal(slotId, slotElement) {
        const modal = document.createElement('div');
        modal.className = 'instructor-modal';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'instructor-modal-content';
        
        // Add title
        const title = document.createElement('h3');
        title.className = 'instructor-modal-title';
        title.textContent = 'Seleccionar Instructor';
        modalContent.appendChild(title);
        
        // Add instructors list
        const instructorsList = document.createElement('div');
        instructorsList.className = 'instructor-list';
        
        availableInstructors.forEach(instructor => {
            const instructorButton = createInstructorButton(instructor, slotId, slotElement, modal);
            instructorsList.appendChild(instructorButton);
        });
        
        modalContent.appendChild(instructorsList);
        
        // Add cancel button
        const cancelButton = document.createElement('button');
        cancelButton.textContent = 'Cancelar';
        cancelButton.className = 'instructor-modal-cancel';
        cancelButton.addEventListener('click', () => {
            modal.remove();
        });
        modalContent.appendChild(cancelButton);
        
        modal.appendChild(modalContent);
        return modal;
    }
    
    function createInstructorButton(instructor, slotId, slotElement, modal) {
        const button = document.createElement('button');
        button.textContent = `${instructor.first_name} ${instructor.last_name} (${instructor.username})`;
        button.className = 'instructor-button';
        button.addEventListener('click', () => {
            assignInstructor(slotId, 'assign', instructor.id, slotElement);
            modal.remove();
        });
        return button;
    }
    
    // ============================================================================
    // API CALL FUNCTIONS
    // ============================================================================
    
    function changeSlotStatus(slotId, action, newStatus, slotElement) {
        const confirmationMessage = getConfirmationMessage(action, slotElement);
        const confirmed = confirm(confirmationMessage);
        
        if (confirmed) {
            showLoadingState(slotElement);
            
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
                    showSuccess(data.message);
                    setTimeout(() => window.location.reload(), 3000);
                } else {
                    showError('Error: ' + data.error);
                    restoreSlotState(slotElement);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showError('Error al cambiar el estado de la sesión');
                restoreSlotState(slotElement);
            });
        }
    }
    
    function assignInstructor(slotId, action, instructorId, slotElement) {
        const confirmationMessage = getInstructorConfirmationMessage(action, slotElement, instructorId);
        const confirmed = confirm(confirmationMessage);
        
        if (confirmed) {
            showLoadingState(slotElement);
            
            fetch(`/scheduler/slot/assign-instructor/${slotId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.csrfToken,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: action,
                    instructor_id: instructorId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showSuccess(data.message);
                    setTimeout(() => window.location.reload(), 3000);
                } else {
                    showError('Error: ' + data.error);
                    restoreSlotState(slotElement);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showError('Error al asignar instructor');
                restoreSlotState(slotElement);
            });
        }
    }
    
    function activatePeriod(periodId, buttonElement) {
        // Show loading state
        const originalText = buttonElement.textContent;
        buttonElement.textContent = 'Procesando...';
        buttonElement.disabled = true;
        
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
                showSuccess('Período activado exitosamente');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showError('Error al activar el período: ' + data.error);
                // Restore button state
                buttonElement.textContent = originalText;
                buttonElement.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error al activar el período:', error);
            showError('Error al activar el período');
            // Restore button state
            buttonElement.textContent = originalText;
            buttonElement.disabled = false;
        });
    }
    
    // ============================================================================
    // UTILITY FUNCTIONS
    // ============================================================================
    
    function getConfirmationMessage(action, slotElement) {
        const date = slotElement.getAttribute('data-date');
        const block = slotElement.getAttribute('data-block');
        const aircraft = slotElement.getAttribute('data-aircraft');
        
        if (action === 'available') {
            return `¿Desea marcar esta sesión como DISPONIBLE?\n\nFecha: ${date}\nBloque: ${block}\nAeronave: ${aircraft}`;
        } else if (action === 'unavailable') {
            return `¿Desea marcar esta sesión como NO DISPONIBLE?\n\nFecha: ${date}\nBloque: ${block}\nAeronave: ${aircraft}`;
        } else if (action === 'cancel_and_unavailable') {
            return `¿Desea cancelar la solicitud de vuelo y marcar esta sesión como NO DISPONIBLE?\n\nFecha: ${date}\nBloque: ${block}\nAeronave: ${aircraft}\n\nEsto cancelará la solicitud de vuelo existente.`;
        }
        return '¿Confirmar acción?';
    }
    
    function getInstructorConfirmationMessage(action, slotElement, instructorId) {
        const date = slotElement.getAttribute('data-date');
        const block = slotElement.getAttribute('data-block');
        const aircraft = slotElement.getAttribute('data-aircraft');
        
        if (action === 'assign') {
            const instructor = availableInstructors.find(inst => inst.id == instructorId);
            const instructorName = instructor ? `${instructor.first_name} ${instructor.last_name}` : 'Instructor';
            return `¿Desea asignar el instructor ${instructorName} a esta sesión?\n\nFecha: ${date}\nBloque: ${block}\nAeronave: ${aircraft}`;
        } else if (action === 'remove') {
            const instructorName = slotElement.getAttribute('data-instructor-name');
            return `¿Desea remover el instructor ${instructorName} de esta sesión?\n\nFecha: ${date}\nBloque: ${block}\nAeronave: ${aircraft}`;
        }
        return '¿Confirmar acción?';
    }
    
    function showError(message) {
        // Create a more user-friendly error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-notification';
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 8 seconds (increased from 5)
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 8000);
    }
    
    function showSuccess(message) {
        // Create a success notification
        const successDiv = document.createElement('div');
        successDiv.className = 'success-notification';
        successDiv.textContent = message;
        document.body.appendChild(successDiv);
        
        // Auto-remove after 5 seconds (increased from 3)
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        }, 5000);
    }
    
    function showLoadingState(slotElement) {
        const slotContent = slotElement.querySelector('.slot-content');
        if (slotContent) {
            slotContent.innerHTML = '<div class="loading-text">Procesando...</div>';
        } else {
            slotElement.textContent = 'Procesando...';
        }
        slotElement.classList.add('slot-loading');
    }
    
    function restoreSlotState(slotElement) {
        slotElement.classList.remove('slot-loading');
        // The page will reload anyway, so we don't need to restore the exact content
    }
});