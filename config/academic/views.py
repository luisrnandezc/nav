from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import StudentGradeForm

@login_required
def submit_student_grade(request):
    """Handle student grade form submission."""
    if request.method == 'POST':
        form = StudentGradeForm(request.POST, instructor=request.user)
        if form.is_valid():
            try:
                form.save()
                return redirect('dashboard:dashboard')
            except Exception as e:
                messages.error(request, f'Error al guardar la forma: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:  
        form = StudentGradeForm(instructor=request.user)

    return render(request, 'academic/student_grade.html', {'form': form})
