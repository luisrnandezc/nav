fetch('course-date.json')
.then(response => response.json())
.then(data => {
    document.getElementById('start-date').textContent = data.start_date;
});