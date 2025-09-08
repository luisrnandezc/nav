document.addEventListener('DOMContentLoaded', function() {
    const subjectSelect = document.querySelector('.subject-edition-select');
    const studentSelect = document.querySelector('.student-select');
    
    // Auto-hide success messages after 5 seconds
    const successMessages = document.querySelectorAll('.message.success');
    successMessages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'opacity 0.5s ease-out';
            message.style.opacity = '0';
            // After fade out, collapse the height
            setTimeout(() => {
                message.style.transition = 'height 0.3s ease-out, margin 0.3s ease-out';
                message.style.height = '0';
                message.style.margin = '0';
                message.style.overflow = 'hidden';
            }, 500);
        }, 5000);
    });
    
    subjectSelect.addEventListener('change', function() {
        const subjectId = this.value;
        if (!subjectId) {
            studentSelect.innerHTML = '<option value="">---------</option>';
            return;
        }
        
        // Show loading state
        studentSelect.innerHTML = '<option value="">Cargando...</option>';
        
        // Fetch students for the selected subject
        fetch(`/academic/ajax/load-students/?subject_edition=${subjectId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error:', data.error);
                    studentSelect.innerHTML = '<option value="">Error al cargar estudiantes</option>';
                    return;
                }
                
                // Clear and populate student select
                studentSelect.innerHTML = '<option value="">---------</option>';
                data.students.forEach(student => {
                    const option = document.createElement('option');
                    option.value = student.id;
                    option.textContent = student.name;
                    studentSelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error:', error);
                studentSelect.innerHTML = '<option value="">Error al cargar estudiantes</option>';
            });
    });
});

function confirmSubmit() {
    return confirm('¿Está seguro que desea guardar las notas? Esta acción no se puede deshacer.');
}