from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import Student, Instructor, Staff

@login_required
def dashboard(request):
    user = request.user
    student_profile = None
    instructor_profile = None
    staff_profile = None

    # Check if the user is a student
    try:
        student_profile = Student.objects.get(user=user)
        context = {
            'user': user,
            'user_profile': student_profile,
        }
        return render(request, "dashboard/student_dashboard.html", context)
    except Student.DoesNotExist:
        pass

    # Check if the user is an instructor
    try:
        instructor_profile = Instructor.objects.get(user=user)
        context = {
            'user': user,
            'user_profile': instructor_profile,
        }
        return render(request, "dashboard/instructor_dashboard.html", context)
    except Instructor.DoesNotExist:
        pass

    # Check if the user is staff
    try:
        staff_profile = Staff.objects.get(user=user)
        context = {
            'user': user,
            'user_profile': staff_profile,
        }
        return render(request, "dashboard/staff_dashboard.html", context) # TODO: eventually this should render a staff dashboard.
    except Staff.DoesNotExist:
        pass

    # TODO: this last render should redirect to an invalid user profile page.
    return render(request, "dashboard/student_dashboard.html", context)
