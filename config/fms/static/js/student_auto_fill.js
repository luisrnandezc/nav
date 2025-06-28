document.addEventListener('DOMContentLoaded', function() {
    const studentIdField = document.getElementById('id_student_id');
    
    if (!studentIdField) return;

    studentIdField.addEventListener('input', function() {
        const studentId = this.value.trim();
        
        if (studentId.length === 0) {
            // Clear all fields when student ID is empty
            const flightHoursField = document.getElementById('id_accumulated_flight_hours');
            const simHoursField = document.getElementById('id_accumulated_sim_hours');
            
            if (flightHoursField) flightHoursField.value = '';
            if (simHoursField) simHoursField.value = '';
            return;
        }
        
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

                        // Determine form type and update only relevant field
                        const isFlightForm = document.getElementById('id_accumulated_flight_hours') !== null;
                        const isSimForm = document.getElementById('id_accumulated_sim_hours') !== null;

                        // Update flight hours and sim hours based on form type
                        if (isFlightForm && data.data.flight_hours !== null) {
                            document.getElementById('id_accumulated_flight_hours').value = data.data.flight_hours;
                        }
                        
                        if (isSimForm && data.data.sim_hours !== null) {
                            document.getElementById('id_accumulated_sim_hours').value = data.data.sim_hours;
                        }
                    } else {
                        // Clear fields on error
                        const flightHoursField = document.getElementById('id_accumulated_flight_hours');
                        const simHoursField = document.getElementById('id_accumulated_sim_hours');
                        
                        if (flightHoursField) flightHoursField.value = '';
                        if (simHoursField) simHoursField.value = '';
                    }
                })
                .catch(error => {
                    console.log('Error:', error);
                    // Clear fields on network error
                    const flightHoursField = document.getElementById('id_accumulated_flight_hours');
                    const simHoursField = document.getElementById('id_accumulated_sim_hours');
                    
                    if (flightHoursField) flightHoursField.value = '';
                    if (simHoursField) simHoursField.value = '';
                });
        }
    });
}); 