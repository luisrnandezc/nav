// Auto-update risk value when severity or probability changes
document.addEventListener('DOMContentLoaded', function() {
    const severitySelect = document.querySelector('select[name="severity"]');
    const probabilitySelect = document.querySelector('select[name="probability"]');
    const valueDisplay = document.getElementById('risk-value-display');
    
    function updateRiskValue() {
        const severity = severitySelect ? severitySelect.value : '';
        const probability = probabilitySelect ? probabilitySelect.value : '';
        
        if (severity && probability) {
            valueDisplay.textContent = severity + probability;
        } else {
            valueDisplay.textContent = 'Seleccione Severidad y Probabilidad';
        }
    }
    
    // Update on change
    if (severitySelect) {
        severitySelect.addEventListener('change', updateRiskValue);
    }
    if (probabilitySelect) {
        probabilitySelect.addEventListener('change', updateRiskValue);
    }
    
    // Initial update
    updateRiskValue();
});