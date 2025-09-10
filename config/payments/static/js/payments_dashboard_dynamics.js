document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.confirm-button').forEach(function(button) {
    button.addEventListener('click', function() {
      const paymentId = this.getAttribute('data-payment-id');
      confirmPayment(paymentId);
    });
  });

  document.querySelectorAll('.unconfirm-button').forEach(function(button) {
    button.addEventListener('click', function() {
      const paymentId = this.getAttribute('data-payment-id');
      unconfirmPayment(paymentId);
    });
  });
});

function confirmPayment(paymentId) {
  if (!confirm('¿Está seguro de que desea confirmar este pago?')) {
    return;
  }

  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  fetch(`/payments/confirm/${paymentId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json',
    },
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      location.reload();
    } else {
      alert('Error: ' + data.error);
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Error al confirmar el pago');
  });
}

function unconfirmPayment(paymentId) {
  if (!confirm('¿Está seguro de que desea desconfirmar este pago?')) {
    return;
  }

  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  fetch(`/payments/unconfirm/${paymentId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json',
    },
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      location.reload();
    } else {
      alert('Error: ' + data.error);
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Error al desconfirmar el pago');
  });
}
