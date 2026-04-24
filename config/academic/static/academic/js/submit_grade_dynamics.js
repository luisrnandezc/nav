document.addEventListener('DOMContentLoaded', function() {
    const subjectSelect = document.querySelector('.subject-edition-select');
    const studentSelect = document.querySelector('.student-select');
    const componentSelect = document.querySelector('.component-select');

    const successMessages = document.querySelectorAll('.message.success');
    successMessages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'opacity 0.5s ease-out';
            message.style.opacity = '0';
            setTimeout(() => {
                message.style.transition = 'height 0.3s ease-out, margin 0.3s ease-out';
                message.style.height = '0';
                message.style.margin = '0';
                message.style.overflow = 'hidden';
            }, 500);
        }, 5000);
    });

    function loadComponents(subjectId) {
        if (!componentSelect) {
            return;
        }
        if (!subjectId) {
            componentSelect.innerHTML = '<option value="">---------</option>';
            return;
        }
        componentSelect.innerHTML = '<option value="">Cargando...</option>';
        fetch(`/academic/ajax/load-grading-components/?subject_edition=${subjectId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error:', data.error);
                    componentSelect.innerHTML = '<option value="">Error al cargar componentes</option>';
                    return;
                }
                componentSelect.innerHTML = '<option value="">---------</option>';
                (data.components || []).forEach(c => {
                    const option = document.createElement('option');
                    option.value = c.id;
                    option.textContent = c.label;
                    componentSelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error:', error);
                componentSelect.innerHTML = '<option value="">Error al cargar componentes</option>';
            });
    }

    if (subjectSelect) {
        subjectSelect.addEventListener('change', function() {
            const subjectId = this.value;
            if (!subjectId) {
                if (studentSelect) {
                    studentSelect.innerHTML = '<option value="">---------</option>';
                }
                loadComponents('');
                return;
            }

            if (studentSelect) {
                studentSelect.innerHTML = '<option value="">Cargando...</option>';
                fetch(`/academic/ajax/load-students/?subject_edition=${subjectId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            console.error('Error:', data.error);
                            studentSelect.innerHTML = '<option value="">Error al cargar estudiantes</option>';
                            return;
                        }
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
            }

            loadComponents(subjectId);
        });
    }
});

function confirmSubmit() {
    return confirm('¿Está seguro que desea guardar las notas? Esta acción no se puede deshacer.');
}
