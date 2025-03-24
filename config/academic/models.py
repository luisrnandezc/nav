from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import Instructor, Student

# Course Model (General)
class Course(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

# Subject Model (Belongs to a Course)
class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Instructor, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.course.name} - {self.name}"

# Enrollment Model (Many-to-Many Relationship)
class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('student', 'subject')

    def __str__(self):
        return f"{self.student.user.username} enrolled in {self.subject.name}"

# Grade Model
class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    attempt = models.PositiveIntegerField(default=1)
    score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])

    class Meta:
        unique_together = ('student', 'subject', 'attempt')

    def __str__(self):
        return f"{self.student.user.username} - {self.subject.name} (Attempt {self.attempt}): {self.score}"