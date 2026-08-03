function confirmSubmission() {
  return confirm(
    '¿Está seguro que desea generar el RER? Esta acción no se puede deshacer.',
  );
}

document.addEventListener('DOMContentLoaded', function () {
  const radioButtons = document.querySelectorAll('input[name="selected_risk"]');
  const severityField = document.querySelector(
    'select[name="post_evaluation_severity"]',
  );
  const probabilityField = document.querySelector(
    'select[name="post_evaluation_probability"]',
  );
  const mitigationCards = document.querySelectorAll('.risk-mitigation-card');
  const riskDataElement = document.getElementById('risk-evaluation-data');
  const riskData = riskDataElement ? JSON.parse(riskDataElement.textContent) : {};

  function updateSelectedRisk(riskId, updateEvaluationFields) {
    mitigationCards.forEach(function (card) {
      card.hidden = card.dataset.riskId !== riskId;
    });

    if (updateEvaluationFields && riskData[riskId]) {
      if (severityField) {
        severityField.value = riskData[riskId].severity;
      }
      if (probabilityField) {
        probabilityField.value = riskData[riskId].probability;
      }
    }
  }

  radioButtons.forEach(function (radio) {
    radio.addEventListener('change', function () {
      if (this.checked) {
        updateSelectedRisk(this.value, true);
      }
    });
  });

  const selectedRadio = document.querySelector(
    'input[name="selected_risk"]:checked',
  );
  updateSelectedRisk(selectedRadio ? selectedRadio.value : '', false);
});
