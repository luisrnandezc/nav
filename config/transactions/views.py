from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, JsonResponse
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.core.cache import cache
from django.db.models import Q
from django.urls import reverse
from urllib.parse import urlencode
from decimal import Decimal
from .models import StudentTransaction
from .services import record_late_fuel
from .forms import StudentTransactionForm, FuelTransactionSearchForm
from accounts.models import StudentProfile, User
from fms.models import FlightEvaluation0_100, FlightEvaluation100_120, FlightEvaluation120_170


FUEL_EVALUATION_MODELS = (
    (FlightEvaluation0_100, 'flightevaluation0_100', 'Evaluación 0-100'),
    (FlightEvaluation100_120, 'flightevaluation100_120', 'Evaluación 100-120'),
    (FlightEvaluation120_170, 'flightevaluation120_170', 'Evaluación 120-170'),
)


@login_required
@permission_required('accounts.can_manage_transactions', raise_exception=True)
def student_overview(request):
    """Let authorized staff search for a student and inspect their full activity."""
    from fms.statistics import calculate_student_stats
    from .student_activity import student_activity

    active_role = request.session.get('selected_role') or request.user.role
    if active_role != User.Role.STAFF:
        raise PermissionDenied('Acceso exclusivo para personal autorizado.')

    search_term = (request.GET.get('q') or '').strip()
    student_results = StudentProfile.objects.none()
    if search_term:
        student_results = StudentProfile.objects.select_related('user').filter(
            user__role=User.Role.STUDENT,
        )
        if search_term.isdigit():
            student_results = student_results.filter(user__national_id=int(search_term))
        else:
            student_results = student_results.filter(
                Q(user__first_name__icontains=search_term)
                | Q(user__last_name__icontains=search_term)
                | Q(user__username__icontains=search_term)
            )
        student_results = student_results.order_by('user__first_name', 'user__last_name')[:20]

    selected_student = (request.GET.get('student') or '').strip()
    profile = None
    if selected_student:
        if not selected_student.isdigit():
            raise Http404('Estudiante no encontrado.')
        profile = get_object_or_404(
            StudentProfile.objects.select_related('user'),
            user__role=User.Role.STUDENT,
            user__national_id=selected_student,
        )

    context = {
        'profile': profile,
        'search_term': search_term,
        'student_results': student_results,
    }
    if profile is None:
        return render(request, 'transactions/student_overview.html', context)

    context = student_activity(profile)
    flight_stats = calculate_student_stats(profile)
    nav_hours = flight_stats['total_flight_hours']
    context.update({
        'nav_total_hours': nav_hours,
        'liters_per_hour': flight_stats['fuel_rate_liters'] if nav_hours else None,
        'dollars_per_hour': flight_stats['flight_hour_cost'] if nav_hours else None,
        'aircraft_summaries': [
            {
                'registration': registration,
                'has_hours': bool(flight_stats[f'total_flight_hours_{key}']),
                'liters_per_hour': flight_stats[f'fuel_rate_liters_{key}'],
                'fuel_cost_per_hour': flight_stats[f'fuel_hour_cost_{key}'],
                'total_cost_per_hour': flight_stats[f'flight_hour_cost_{key}'],
            }
            for registration, key in (('YV204E', 'yv204e'), ('YV206E', 'yv206e'))
        ],
    })
    rows = context.pop('movements')
    kind = request.GET.get('type', '')
    if kind == 'credits':
        rows = [row for row in rows if row['credit']]
    elif kind == 'debits':
        rows = [row for row in rows if not row['credit']]
    elif kind == 'flights':
        rows = [row for row in rows if row['flight']]
    for key in ('start', 'end'):
        try:
            value = parse_date(request.GET.get(key, ''))
        except ValueError:
            value = None
        if value:
            rows = [row for row in rows if (row['date'] >= value if key == 'start' else row['date'] <= value)]
        context[key] = value.isoformat() if value else ''
    if request.GET.get('movement', '').isdigit():
        rows = [row for row in rows if row['id'] == f'transaction-{request.GET["movement"]}']
    params = request.GET.copy()
    params.pop('page', None)
    context.update({
        'profile': profile, 'page_obj': Paginator(rows, 25).get_page(request.GET.get('page')),
        'filter_type': kind, 'query': params.urlencode(), 'search_term': search_term,
        'student_results': student_results,
    })
    return render(request, 'transactions/student_overview.html', context)


def get_evaluations_without_fuel(student_id=None):
    """Return all evaluations without fuel, optionally filtered by student."""
    evaluations = []

    for model, model_type, model_name in FUEL_EVALUATION_MODELS:
        queryset = model.objects.filter(fuel_consumed=Decimal('0')).select_related('aircraft')
        if student_id is not None:
            queryset = queryset.filter(student_id=student_id)

        evaluations.extend({
            'evaluation': evaluation,
            'model_type': model_type,
            'model_name': model_name,
        } for evaluation in queryset)

    return sorted(
        evaluations,
        key=lambda item: (item['evaluation'].session_date, item['evaluation'].pk),
        reverse=True,
    )


def fuel_results_redirect(active_student_filter=None):
    """Return to the fuel results while preserving an intentional filter."""
    results_url = reverse('transactions:add_fuel_transaction')
    if active_student_filter is not None:
        results_url = f'{results_url}?{urlencode({"student_national_id": active_student_filter})}'
    return redirect(results_url)


@login_required
@permission_required('accounts.can_manage_transactions')
def transactions_dashboard(request):
    """Transactions Dashboard view: unconfirmed and confirmed in separate lists.
    Only shows transactions for students with student_phase=FLYING.
    Optional GET 'q': filter by student name or national_id (same logic as FMS user search)."""
    search_term = (request.GET.get('q') or '').strip()

    base_qs = StudentTransaction.objects.select_related(
        'student_profile__user',
        'added_by',
        'confirmed_by',
    ).filter(student_profile__student_phase=StudentProfile.FLYING).order_by('-date_added')

    if search_term:
        if search_term.isdigit():
            try:
                matching_profiles = StudentProfile.objects.filter(
                    student_phase=StudentProfile.FLYING,
                    user__role='STUDENT',
                    user__national_id=int(search_term),
                )
            except (ValueError, TypeError):
                matching_profiles = StudentProfile.objects.none()
        else:
            matching_users = User.objects.filter(
                role='STUDENT',
            ).filter(
                Q(first_name__icontains=search_term) | Q(last_name__icontains=search_term),
            ).values_list('id', flat=True)[:20]
            matching_profiles = StudentProfile.objects.filter(
                student_phase=StudentProfile.FLYING,
                user_id__in=matching_users,
            )
        base_qs = base_qs.filter(student_profile__in=matching_profiles)

    unconfirmed_transactions = base_qs.filter(confirmed=False)[:50]
    confirmed_transactions = base_qs.filter(confirmed=True)[:50]

    can_confirm_transactions = request.user.has_perm('accounts.can_confirm_transactions')

    context = {
        'unconfirmed_transactions': unconfirmed_transactions,
        'confirmed_transactions': confirmed_transactions,
        'can_confirm_transactions': can_confirm_transactions,
        'search_term': search_term,
    }
    return render(request, 'transactions/transactions_dashboard.html', context)


@login_required
def confirm_transaction(request, transaction_id):
    """Confirm a transaction - only for users with permission."""
    
    can_confirm_transactions = request.user.has_perm('accounts.can_confirm_transactions')
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    if not can_confirm_transactions:
        return JsonResponse({'success': False, 'error': 'No tiene permisos para confirmar transacciones'})
    
    try:
        transaction = get_object_or_404(StudentTransaction, id=transaction_id)
        
        if transaction.confirmed:
            return JsonResponse({'success': False, 'error': 'La transacción ya ha sido confirmada'})
        
        transaction.confirm(request.user)
        
        return JsonResponse({
            'success': True, 
            'message': 'Transacción confirmada exitosamente',
            'confirmed_by': f"{request.user.first_name} {request.user.last_name}",
            'confirmation_date': transaction.confirmation_date.strftime('%d/%m/%Y %H:%M')
        })
        
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        import traceback
        print(f"Error in confirm_transaction: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})


@login_required
def unconfirm_transaction(request, transaction_id):
    """Unconfirm a transaction - only for users with permission."""
    can_confirm_transactions = request.user.has_perm('accounts.can_confirm_transactions')
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    if not can_confirm_transactions:
        return JsonResponse({'success': False, 'error': 'No tiene permisos para desconfirmar transacciones'})
    
    try:
        transaction = get_object_or_404(StudentTransaction, id=transaction_id)
        
        if not transaction.confirmed:
            return JsonResponse({'success': False, 'error': 'La transacción no está confirmada'})
        
        transaction.unconfirm()
        
        return JsonResponse({
            'success': True, 
            'message': 'Transacción desconfirmada exitosamente'
        })
        
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'An error occurred'})


@login_required
@permission_required('accounts.can_manage_transactions')
def add_transaction(request):
    """Add new transaction form view."""
    if request.method == 'POST':
        cache_key = f"transaction_rate_limit_{request.user.id}"
        transaction_count = cache.get(cache_key, 0)
        
        if transaction_count >= 20:
            messages.error(request, 'Has alcanzado el límite de transacciones por hora. Intenta más tarde.')
            form = StudentTransactionForm(user=request.user)
            return render(request, 'transactions/add_transaction.html', {'form': form})
        
        form = StudentTransactionForm(request.POST, user=request.user)
        if form.is_valid():
            if not request.user.has_perm('accounts.can_manage_transactions'):
                messages.error(request, 'Solo el personal autorizado puede agregar transacciones.')
                return render(request, 'transactions/add_transaction.html', {'form': form})
            
            try:
                transaction = form.save(commit=False)
                transaction.added_by = request.user
                
                # If transaction is being confirmed, set confirmed_by
                if transaction.confirmed:
                    transaction.confirmed_by = request.user
                    transaction.confirmation_date = timezone.now()
                
                transaction.save()
                
                cache.set(cache_key, transaction_count + 1, 3600)
                
                return redirect('transactions:transactions_dashboard')
            except ValidationError as e:
                messages.error(request, f'Error al guardar la transacción: {str(e)}')
                return render(request, 'transactions/add_transaction.html', {'form': form})
    else:
        form = StudentTransactionForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'transactions/add_transaction.html', context)


@login_required
@permission_required('accounts.can_manage_transactions')
def transaction_detail(request, transaction_id):
    """Transaction detail view showing full transaction information."""
    transaction = get_object_or_404(
        StudentTransaction.objects.select_related(
            'student_profile__user', 
            'added_by', 
            'confirmed_by'
        ), 
        id=transaction_id
    )
    
    can_confirm_transactions = request.user.has_perm('accounts.can_confirm_transactions')
    
    context = {
        'transaction': transaction,
        'can_confirm_transactions': can_confirm_transactions,
    }
    
    return render(request, 'transactions/transaction_detail.html', context)

@login_required
@permission_required('accounts.can_manage_transactions')
def add_fuel_transaction(request):
    """List evaluations with missing fuel data, optionally filtered by student."""
    student_profile = None
    active_student_filter = None
    form_data = request.GET.copy()

    # Keep old bookmarked/redirected URLs working.
    if 'student_id' in form_data and 'student_national_id' not in form_data:
        form_data['student_national_id'] = form_data['student_id']

    search_form = FuelTransactionSearchForm(form_data or None)
    if form_data and search_form.is_valid():
        active_student_filter = search_form.cleaned_data.get('student_national_id')
        if active_student_filter is not None:
            student_profile = StudentProfile.objects.select_related('user').get(
                user__national_id=active_student_filter
            )

    evaluations = get_evaluations_without_fuel(active_student_filter)
    
    context = {
        'search_form': search_form,
        'evaluations': evaluations,
        'student_profile': student_profile,
        'active_student_filter': active_student_filter,
    }
    
    return render(request, 'transactions/add_fuel_transaction.html', context)


@login_required
@permission_required('accounts.can_manage_transactions')
def update_fuel_consumed(request):
    """Update fuel_consumed for a specific flight evaluation and create a StudentTransaction record."""
    active_student_filter = None
    
    if request.method == 'POST':
        evaluation_id = request.POST.get('evaluation_id')
        model_type = request.POST.get('model_type')
        fuel_consumed = request.POST.get('fuel_consumed')
        filter_value = (request.POST.get('active_student_filter') or '').strip()
        if filter_value.isdigit():
            active_student_filter = int(filter_value)
        
        if not all([evaluation_id, model_type, fuel_consumed]):
            messages.error(request, 'Faltan datos requeridos.')
            return fuel_results_redirect(active_student_filter)
        
        try:
            fuel_consumed = Decimal(fuel_consumed)
            if not fuel_consumed.is_finite() or fuel_consumed < Decimal('0.1') or fuel_consumed > 1000 or fuel_consumed != fuel_consumed.quantize(Decimal('0.1')):
                messages.error(request, 'El volumen de combustible debe estar entre 0.1 y 1000 litros.')
                return fuel_results_redirect(active_student_filter)
            
            # Map model type to model class
            model_map = {
                'flightevaluation0_100': FlightEvaluation0_100,
                'flightevaluation100_120': FlightEvaluation100_120,
                'flightevaluation120_170': FlightEvaluation120_170,
            }
            
            model_class = model_map.get(model_type)
            if not model_class:
                messages.error(request, 'Tipo de evaluación inválido.')
                return fuel_results_redirect(active_student_filter)
            
            record_late_fuel(
                model_class, evaluation_id, fuel_consumed, request.user,
                observations=request.POST.get('observations', ''),
            )
            
            messages.success(request, f'Combustible actualizado exitosamente: {fuel_consumed} litros.')
            
        except (ValueError, TypeError):
            messages.error(request, 'El volumen de combustible debe ser un número válido.')
        except (FlightEvaluation0_100.DoesNotExist, FlightEvaluation100_120.DoesNotExist, FlightEvaluation120_170.DoesNotExist):
            messages.error(request, 'Evaluación no encontrada.')
        except StudentProfile.DoesNotExist:
            messages.error(request, 'Perfil de estudiante no encontrado.')
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error al actualizar: {str(e)}')

    return fuel_results_redirect(active_student_filter)
