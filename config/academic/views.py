from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from decimal import Decimal

from .forms import StudentGradeForm
from .models import SubjectEdition, StudentGrade
from accounts.models import User


@login_required
def submit_student_grade(request):
    """Handle student grade form submission."""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_temp':
            form = StudentGradeForm(request.POST, instructor=request.user)

            if form.is_valid():
                temp_grades = request.session.get('temp_grades', [])
                comp = form.cleaned_data['component']
                edition = form.cleaned_data['subject_edition']
                label = dict(StudentGrade._meta.get_field('component').choices).get(comp, comp)
                grade_data = {
                    'subject_edition_id': edition.id,
                    'component': comp,
                    'component_label': label,
                    'student_id': form.cleaned_data['student'].id,
                    'instructor_id': request.user.id,
                    'grade': float(form.cleaned_data['grade']),
                    'test_type': form.cleaned_data['test_type'],
                    'test_type_display': dict(StudentGrade._meta.get_field('test_type').choices)[
                        form.cleaned_data['test_type']
                    ],
                }

                if not any(
                    g['subject_edition_id'] == grade_data['subject_edition_id']
                    and g['student_id'] == grade_data['student_id']
                    and g['component'] == grade_data['component']
                    and g['test_type'] == grade_data['test_type']
                    for g in temp_grades
                ):
                    temp_grades.append(grade_data)
                    request.session['temp_grades'] = temp_grades
                    messages.success(request, 'Calificación agregada temporalmente')
                else:
                    messages.error(
                        request,
                        'Ya existe una calificación temporal para este estudiante con el mismo tipo de examen',
                    )

                return redirect('academic:submit_grade')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

        elif action == 'submit_all':
            temp_grades = request.session.get('temp_grades', [])
            if not temp_grades:
                messages.error(request, 'No hay calificaciones para guardar')
                return redirect('academic:submit_grade')

            success_count = 0
            for grade_data in temp_grades:
                try:
                    StudentGrade.objects.create(
                        subject_edition_id=grade_data['subject_edition_id'],
                        component=grade_data['component'],
                        student_id=grade_data['student_id'],
                        instructor_id=grade_data['instructor_id'],
                        grade=grade_data['grade'],
                        test_type=grade_data['test_type'],
                    )
                    success_count += 1
                except Exception as e:
                    messages.error(request, f'Error al guardar la calificación: {str(e)}')

            if success_count > 0:
                messages.success(request, f'Se guardaron {success_count} calificaciones exitosamente')
                request.session.pop('temp_grades', None)
                return redirect('academic:submit_grade')

        elif action == 'clear_temp':
            request.session.pop('temp_grades', None)
            messages.success(request, 'Calificaciones temporales eliminadas')
            return redirect('academic:submit_grade')

        elif action == 'delete_temp':
            grade_index = request.POST.get('grade_index')
            if grade_index is not None:
                try:
                    grade_index = int(grade_index)
                    temp_grades = request.session.get('temp_grades', [])
                    if 0 <= grade_index < len(temp_grades):
                        deleted_grade = temp_grades.pop(grade_index)
                        request.session['temp_grades'] = temp_grades
                        try:
                            s = User.objects.get(id=deleted_grade['student_id'])
                            label = f'{s.first_name} {s.last_name}'
                        except User.DoesNotExist:
                            label = 'el estudiante'
                        messages.success(request, f'Calificación de {label} eliminada')
                    else:
                        messages.error(request, 'Índice de calificación inválido')
                except (ValueError, TypeError):
                    messages.error(request, 'Índice de calificación inválido')
            else:
                messages.error(request, 'No se proporcionó el índice de la calificación')
            return redirect('academic:submit_grade')

    form = StudentGradeForm(instructor=request.user)
    raw_temp = request.session.get('temp_grades', [])
    temp_grades = []
    for grade in raw_temp:
        try:
            subject = SubjectEdition.objects.select_related('subject_type').get(id=grade['subject_edition_id'])
            student = User.objects.get(id=grade['student_id'])
            grade['subject_name'] = subject.subject_type.name
            grade['student_name'] = f'{student.first_name} {student.last_name}'
            temp_grades.append(grade)
        except (SubjectEdition.DoesNotExist, User.DoesNotExist):
            continue
    if len(temp_grades) != len(raw_temp):
        request.session['temp_grades'] = temp_grades

    return render(request, 'academic/submit_grade.html', {
        'form': form,
        'temp_grades': temp_grades,
    })


@login_required
def load_students(request):
    """AJAX view to load students for a subject edition."""
    subject_edition_id = request.GET.get('subject_edition')
    if not subject_edition_id:
        return JsonResponse({'error': 'No se proporcionó una edición de materia'}, status=400)

    try:
        subject_edition = SubjectEdition.objects.select_related('instructor').get(id=subject_edition_id)
        if subject_edition.instructor != request.user:
            return JsonResponse({'error': 'Instructor no autorizado'}, status=403)

        students = subject_edition.students.all().order_by('first_name', 'last_name')
        student_list = [{'id': s.id, 'name': f'{s.first_name} {s.last_name}'} for s in students]
        return JsonResponse({'students': student_list})
    except SubjectEdition.DoesNotExist:
        return JsonResponse({'error': 'Edición de materia no encontrada'}, status=404)


@login_required
def load_grading_components(request):
    """AJAX: theory/practical options for a subject edition (values are codes, not ids)."""
    subject_edition_id = request.GET.get('subject_edition')
    if not subject_edition_id:
        return JsonResponse({'error': 'No se proporcionó una edición de materia'}, status=400)
    try:
        subject_edition = SubjectEdition.objects.select_related('instructor').get(id=subject_edition_id)
        if subject_edition.instructor != request.user:
            return JsonResponse({'error': 'Instructor no autorizado'}, status=403)

        eps = Decimal('0.001')
        data = []
        if subject_edition.theory_weight > eps:
            data.append({
                'code': 'theory',
                'label': f'Teoría (peso {subject_edition.theory_weight})',
            })
        if subject_edition.practical_weight > eps:
            data.append({
                'code': 'practical',
                'label': f'Práctica (peso {subject_edition.practical_weight})',
            })
        return JsonResponse({'components': data})
    except SubjectEdition.DoesNotExist:
        return JsonResponse({'error': 'Edición de materia no encontrada'}, status=404)


@login_required
def grade_logs(request):
    user = request.user
    grade_logs = StudentGrade.objects.filter(student=user).select_related(
        'subject_edition__subject_type', 'instructor'
    ).order_by('-date')[:10]
    return render(request, 'academic/grade_log.html', {'grade_logs': grade_logs, 'user': user})


@login_required
def instructor_grades_dashboard(request):
    user = request.user
    recent_grades = StudentGrade.objects.filter(instructor=user).select_related(
        'student', 'subject_edition__subject_type'
    ).order_by('-date')[:30]
    return render(request, 'academic/instructor_grades_dashboard.html', {
        'recent_grades': recent_grades,
        'user': user,
    })
