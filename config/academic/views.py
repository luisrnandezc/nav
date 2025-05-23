from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import StudentGradeForm
from .models import SubjectEdition
from accounts.models import User


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

    return render(request, 'academic/submit_grade.html', {'form': form})

@login_required
def load_students(request):
    """AJAX view to load students for a subject edition."""
    subject_edition_id = request.GET.get('subject_edition')
    if not subject_edition_id:
        return JsonResponse({'error': 'No se proporcionó una edición de materia'}, status=400)
    
    try:
        subject_edition = SubjectEdition.objects.get(id=subject_edition_id)
        # Verify the instructor has access to this subject edition
        if subject_edition.instructor != request.user:
            return JsonResponse({'error': 'Instructor no autorizado'}, status=403)
        
        # Get all students enrolled in this subject edition
        students = subject_edition.students.all().order_by('first_name', 'last_name')
        
        student_list = [{'id': student.id, 'name': f"{student.first_name} {student.last_name}"} 
                       for student in students]
        return JsonResponse({'students': student_list})
    except SubjectEdition.DoesNotExist:
        return JsonResponse({'error': 'Edición de materia no encontrada'}, status=404)
