// Add confirmation dialog to all fuel update forms
document.addEventListener('DOMContentLoaded', function() {
const fuelUpdateForms = document.querySelectorAll('.fuel-update-form');

fuelUpdateForms.forEach(function(form) {
    const litersInput = form.querySelector('input[name="fuel_consumed"]');
    const preview = form.querySelector('.fuel-charge-preview');
    const price = Number(form.dataset.fuelPrice);
    litersInput.addEventListener('input', function() {
        const liters = Number(litersInput.value);
        preview.textContent = liters > 0 && Number.isFinite(liters)
            ? `${liters} L × $${price.toFixed(2)}/L = $${(liters * price).toFixed(2)} de débito. Se aplicará al saldo al guardar.`
            : `Tarifa: $${price.toFixed(2)}/L. Ingrese los litros para ver el débito.`;
    });
    form.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const fuelInput = form.querySelector('input[name="fuel_consumed"]');
    const fuelValue = fuelInput.value;
    
    if (!fuelValue || parseFloat(fuelValue) <= 0) {
        return; // Let browser validation handle this
    }
    
    const confirmMessage = preview.textContent + '\n\n¿Registrar este combustible y aplicar el débito al estudiante?';
    
    if (confirm(confirmMessage)) {
        form.submit();
    }
    });
});
});
