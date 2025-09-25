// Flight Request Dashboard JavaScript
// Handles approve/cancel actions for flight requests

document.addEventListener('DOMContentLoaded', function() {
    // CSRF token is set in the template
    if (typeof window.csrfToken === 'undefined') {
        console.error('CSRF token not found');
    }
});

function approveRequest(requestId) {
    if (confirm('¿Está seguro de que desea aprobar esta solicitud de vuelo?')) {
        fetch(`/scheduler/flight-request/approve/${requestId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.csrfToken,
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Solicitud aprobada exitosamente');
                window.location.reload();
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al aprobar la solicitud');
        });
    }
}

function cancelRequest(requestId) {
    if (confirm('¿Está seguro de que desea cancelar esta solicitud de vuelo?')) {
        fetch(`/scheduler/flight-request/cancel/${requestId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.csrfToken,
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Solicitud cancelada exitosamente');
                window.location.reload();
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cancelar la solicitud');
        });
    }
}
