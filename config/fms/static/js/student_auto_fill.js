document.addEventListener('DOMContentLoaded', function() {
    const studentIdField = document.getElementById('id_student_id');
    
    if (!studentIdField) return;

    studentIdField.addEventListener('input', function() {
        const studentId = this.value.trim();
        
        if (studentId.length >= 7) {
            fetch(`/fms/api/get_student_data/?student_id=${studentId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Populate fields
                        document.getElementById('id_student_first_name').value = data.data.student_first_name;
                        document.getElementById('id_student_last_name').value = data.data.student_last_name;
                        document.getElementById('id_student_license_type').value = data.data.student_license_type;
                        document.getElementById('id_course_type').value = data.data.course_type;
                    }
                })
                .catch(error => console.log('Error:', error));
        }
    });
}); 