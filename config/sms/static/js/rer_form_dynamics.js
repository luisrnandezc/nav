function confirmSubmission() {
  return confirm(
    '¿Está seguro que desea generar el RER? Esta acción no se puede deshacer.',
  );
}

// Event listener for risk selection
document.addEventListener('DOMContentLoaded', function () {
  const radioButtons = document.querySelectorAll('input[name="selected_risk"]');

  radioButtons.forEach(function (radio) {
    radio.addEventListener('change', function () {
      if (this.checked) {
        // Get the label text associated with this radio button
        const label = document.querySelector('label[for="' + this.id + '"]');
        if (label) {
          const descriptionDiv = label.querySelector('.description-text');
          if (descriptionDiv) {
            const labelText = descriptionDiv.textContent.trim();

            // Extract first two characters
            if (labelText.length >= 2) {
              const firstChar = labelText.charAt(1);
              const secondChar = labelText.charAt(2);

              console.log(firstChar);
              console.log(secondChar);

              // Update the severity field
              const severityField = document.querySelector(
                'select[name="post_evaluation_severity"]',
              );
              if (severityField) {
                severityField.value = firstChar;
              }

              // Update the probability field
              const probabilityField = document.querySelector(
                'select[name="post_evaluation_probability"]',
              );
              if (probabilityField) {
                probabilityField.value = secondChar;
              }
            }
          }
        }
      }
    });
  });
});
