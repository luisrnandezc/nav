// Add confirmation dialog to all fuel update forms
document.addEventListener('DOMContentLoaded', function() {
const fuelUpdateForms = document.querySelectorAll('.fuel-update-form');

fuelUpdateForms.forEach(function(form) {
    form.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const fuelInput = form.querySelector('input[name="fuel_consumed"]');
    const fuelValue = fuelInput.value;
    
    if (!fuelValue || parseFloat(fuelValue) <= 0) {
        return; // Let browser validation handle this
    }
    
    const confirmMessage = 'Advertencia: esta acción no se puede revertir.\n\n¿Está seguro de que desea agregar el combustible especificado a la evaluación de vuelo?';
    
    if (confirm(confirmMessage)) {
        form.submit();
    }
    });
});
});