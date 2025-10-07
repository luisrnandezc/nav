// Student List JavaScript
// Handles toggle permission functionality for directors

document.addEventListener('DOMContentLoaded', function() {
  // Handle toggle permission buttons
  const toggleButtons = document.querySelectorAll('.toggle-permission-btn');
  
  toggleButtons.forEach(button => {
    button.addEventListener('click', function() {
      const studentId = this.getAttribute('data-student-id');
      const studentName = this.getAttribute('data-student-name');
      
      // Show loading state
      const originalText = this.textContent;
      this.textContent = 'Procesando...';
      this.disabled = true;
      
      // Make the request
      fetch('/fms/api/toggle_temp_permission/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': window.csrfToken,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `student_id=${studentId}`
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Update button state
          this.classList.toggle('permission-active');
          this.classList.toggle('permission-inactive');
          
          // Update button text
          if (data.has_temp_permission) {
            this.textContent = '🔒 Desactivar Permiso Temporal';
          } else {
            this.textContent = '🔓 Activar Permiso Temporal';
          }
          
          // Re-enable button
          this.disabled = false;
          
          // Show success message
          showNotification(data.message, 'success');
          
          // Update permission display if visible
          updatePermissionDisplay(studentId, data.has_temp_permission);
          
        } else {
          showNotification('Error: ' + data.error, 'error');
          // Restore button state
          this.textContent = originalText;
          this.disabled = false;
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showNotification('Error al actualizar el permiso', 'error');
        // Restore button state
        this.textContent = originalText;
        this.disabled = false;
      });
    });
  });
  
  function updatePermissionDisplay(studentId, hasPermission) {
    // Find the student item and update the permission display
    const studentItems = document.querySelectorAll('.student-item');
    studentItems.forEach(item => {
      const button = item.querySelector(`[data-student-id="${studentId}"]`);
      if (button) {
        const detailsContainer = item.querySelector('.student-details');
        let permissionDisplay = detailsContainer.querySelector('.temp-permission-display');
        
        if (hasPermission && !permissionDisplay) {
          // Add permission display
          const permissionItem = document.createElement('div');
          permissionItem.className = 'detail-item temp-permission-display';
          permissionItem.innerHTML = `
            <span class="detail-label">Permiso Temporal:</span>
            <span class="detail-value temp-permission-active">Activo</span>
          `;
          detailsContainer.appendChild(permissionItem);
        } else if (!hasPermission && permissionDisplay) {
          // Remove permission display
          permissionDisplay.remove();
        }
      }
    });
  }
  
  function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 5000);
  }
});
