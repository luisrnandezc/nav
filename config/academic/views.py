from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import StudentGradeForm
from .models import SubjectEdition, StudentGrade
from accounts.models import User


@login_required
def submit_student_grade(request):
    """Handle student grade form submission."""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_temp':
            # Handle adding to temporary storage
            form = StudentGradeForm(request.POST, instructor=request.user)
            
            if form.is_valid():
                # Get the temporary grades from session or initialize empty list
                temp_grades = request.session.get('temp_grades', [])
                
                # Add new grade to temporary storage
                grade_data = {
                    'subject_edition': form.cleaned_data['subject_edition'].id,
                    'subject_name': form.cleaned_data['subject_edition'].subject_type.name,
                    'student_id': form.cleaned_data['student'].id,
                    'student_first_name': form.cleaned_data['student'].first_name,
                    'student_last_name': form.cleaned_data['student'].last_name,
                    'instructor_id': request.user.id,
                    'instructor_first_name': request.user.first_name,
                    'instructor_last_name': request.user.last_name,
                    'grade': float(form.cleaned_data['grade']),
                    'test_type': form.cleaned_data['test_type']
                }
                
                # Check for duplicates in temp storage
                if not any(g['subject_edition'] == grade_data['subject_edition'] and 
                          g['student_id'] == grade_data['student_id'] and 
                          g['test_type'] == grade_data['test_type'] 
                          for g in temp_grades):
                    temp_grades.append(grade_data)
                    request.session['temp_grades'] = temp_grades
                    messages.success(request, 'Calificación agregada temporalmente')
                else:
                    messages.error(request, 'Ya existe una calificación temporal para este estudiante con el mismo tipo de examen')
                
                return redirect('academic:submit_grade')
            else:
                # Display form validation errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)
        
        elif action == 'submit_all':
            # Handle final submission of all temporary grades
            temp_grades = request.session.get('temp_grades', [])
            if not temp_grades:
                messages.error(request, 'No hay calificaciones para guardar')
                return redirect('academic:submit_grade')
            
            success_count = 0
            for grade_data in temp_grades:
                try:
                    # Create the grade with all required fields
                    StudentGrade.objects.create(
                        subject_edition_id=grade_data['subject_edition'],
                        student_id=grade_data['student_id'],
                        instructor_id=grade_data['instructor_id'],
                        grade=grade_data['grade'],
                        test_type=grade_data['test_type']
                    )
                    success_count += 1
                except Exception as e:
                    messages.error(request, f'Error al guardar la calificación: {str(e)}')
            
            if success_count > 0:
                messages.success(request, f'Se guardaron {success_count} calificaciones exitosamente')
                # Clear temporary storage
                request.session.pop('temp_grades', None)
                return redirect('dashboard:dashboard')
            
        elif action == 'clear_temp':
            # Clear temporary storage
            request.session.pop('temp_grades', None)
            messages.success(request, 'Calificaciones temporales eliminadas')
            return redirect('academic:submit_grade')
    
    # GET request - display form and temporary grades
    form = StudentGradeForm(instructor=request.user)
    temp_grades = request.session.get('temp_grades', [])
    
    # Get full objects for display
    for grade in temp_grades:
        try:
            subject = SubjectEdition.objects.get(id=grade['subject_edition'])
            grade['subject_name'] = subject.subject_type.name
            grade['student_name'] = f"{grade['student_first_name']} {grade['student_last_name']}"
        except SubjectEdition.DoesNotExist:
            continue

    return render(request, 'academic/submit_grade.html', {
        'form': form,
        'temp_grades': temp_grades
    })


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
