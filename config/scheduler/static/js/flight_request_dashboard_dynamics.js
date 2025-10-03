// Flight Request Dashboard JavaScript
// Handles approve/cancel actions for flight requests

document.addEventListener('DOMContentLoaded', function() {
    // CSRF token is set in the template
    if (typeof window.csrfToken === 'undefined') {
        console.error('CSRF token not found');
    }
    
    // Attach event listeners to cancel buttons
    const buttons = document.querySelectorAll('.student-cancel-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', function(event) {
            event.preventDefault();
            const id = Number(btn.dataset.requestId);
            const date = btn.dataset.requestDate;
            const status = btn.dataset.requestStatus;
            studentCancelRequest(id, date, status);
        });
    });
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

function studentCancelRequest(requestId, requestDateStr, requestStatus) {
    const referenceHour = 12;

    const today = new Date();
    today.setHours(referenceHour, 0, 0, 0);

    const flightDate = new Date(requestDateStr);
    flightDate.setHours(referenceHour, 0, 0, 0);

    const diffMs = flightDate - today;
    const diffHours = diffMs / (1000 * 60 * 60);

    const hasFee = diffHours < 24 && requestStatus === 'approved';
    const confirmMessage = hasFee 
        ? '¿Está seguro de que desea cancelar esta solicitud de vuelo? Se aplicará una multa equivalente a una (1) hora de vuelo por cancelación extemporánea.'
        : '¿Está seguro de que desea cancelar esta solicitud de vuelo?';

    if (confirm(confirmMessage)) {
        fetch(`/scheduler/flight-request/cancel/${requestId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.csrfToken,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                apply_fee: hasFee,
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Solicitud de vuelo cancelada exitosamente.');
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