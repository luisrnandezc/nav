document.addEventListener('DOMContentLoaded', function() {
    const subjectSelect = document.querySelector('.subject-edition-select');
    const studentSelect = document.querySelector('.student-select');
    
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