document.addEventListener('DOMContentLoaded', function() {
  console.log('JavaScript loaded, looking for confirm buttons...');
  const confirmButtons = document.querySelectorAll('.confirm-button');
  console.log('Found confirm buttons:', confirmButtons.length);
  
  confirmButtons.forEach(function(button) {
    button.addEventListener('click', function() {
      console.log('Confirm button clicked!');
      const transactionId = this.getAttribute('data-transaction-id');
      console.log('Transaction ID:', transactionId);
      confirmTransaction(transactionId);
    });
  });

  document.querySelectorAll('.unconfirm-button').forEach(function(button) {
    button.addEventListener('click', function() {
      const transactionId = this.getAttribute('data-transaction-id');
      unconfirmTransaction(transactionId);
    });
  });
});

function confirmTransaction(transactionId) {
  if (!confirm('¿Está seguro de que desea confirmar esta transacción?')) {
    return;
  }

  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  console.log('Making fetch request to:', `/transactions/confirm/${transactionId}/`);
  
  fetch(`/transactions/confirm/${transactionId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json',
    },
  })
  .then(response => {
    console.log('Response status:', response.status);
    console.log('Response headers:', response.headers);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  })
  .then(data => {
    console.log('Response data:', data);
    if (data.success) {
      console.log('Success! Reloading page...');
      location.reload();
    } else {
      console.log('Error from server:', data.error);
      alert('Error: ' + data.error);
    }
  })
  .catch(error => {
    console.error('Fetch error:', error);
    alert('Error al confirmar la transacción: ' + error.message);
  });
}

function unconfirmTransaction(transactionId) {
  if (!confirm('¿Está seguro de que desea desconfirmar esta transacción?')) {
    return;
  }

  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  fetch(`/transactions/unconfirm/${transactionId}/`, {
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
    alert('Error al desconfirmar la transacción');
  });
}
