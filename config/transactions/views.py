from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
from decimal import Decimal
from .models import StudentTransaction
from .forms import StudentTransactionForm, FuelTransactionSearchForm
from accounts.models import StudentProfile
from fms.models import FlightEvaluation0_100, FlightEvaluation100_120, FlightEvaluation120_170
from fleet.models import Aircraft


@login_required
@permission_required('accounts.can_manage_transactions')
def transactions_dashboard(request):
    """Transactions Dashboard view showing latest 50 transactions."""
    latest_transactions = StudentTransaction.objects.select_related(
        'student_profile__user', 
        'added_by', 
        'confirmed_by'
    ).all().order_by('-date_added')[:50]
    
    can_confirm_transactions = request.user.has_perm('accounts.can_confirm_transactions')
    
    context = {
        'latest_transactions': latest_transactions,
        'can_confirm_transactions': can_confirm_transactions,
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
    """Search for student evaluations with missing fuel data and allow updates."""
    from accounts.models import StudentProfile
    from fms.models import FlightEvaluation0_100, FlightEvaluation100_120, FlightEvaluation120_170
    from decimal import Decimal
    from django.db.models import Q
    
    evaluations = []
    student_profile = None
    
    # Check if student_id is in query params (from redirect after update)
    student_id_param = request.GET.get('student_id')
    if student_id_param:
        # Pre-populate form with student_id
        search_form = FuelTransactionSearchForm({'student_national_id': student_id_param})
        # Auto-search if form is valid
        if search_form.is_valid():
            student_id = search_form.cleaned_data['student_national_id']
        else:
            search_form = FuelTransactionSearchForm()
            student_id = None
    else:
        search_form = FuelTransactionSearchForm(request.POST if request.method == 'POST' else None)
        student_id = None
    
    # Perform search if form is valid (either from POST or GET with student_id)
    if (request.method == 'POST' and search_form.is_valid()) or (student_id_param and search_form.is_valid()):
        if not student_id:
            student_id = search_form.cleaned_data['student_national_id']
        
        try:
            student_profile = StudentProfile.objects.get(user__national_id=student_id)
            
            # Search all three evaluation types for evaluations with fuel_consumed = 0.0
            fuel_filter = Q(fuel_consumed=Decimal('0.0')) | Q(fuel_consumed=0) | Q(fuel_consumed=Decimal('0'))
            
            # Get evaluations from all three models
            evals_0_100 = FlightEvaluation0_100.objects.filter(
                student_id=student_id
            ).filter(fuel_filter).select_related('aircraft').order_by('-session_date', '-id')
            
            evals_100_120 = FlightEvaluation100_120.objects.filter(
                student_id=student_id
            ).filter(fuel_filter).select_related('aircraft').order_by('-session_date', '-id')
            
            evals_120_170 = FlightEvaluation120_170.objects.filter(
                student_id=student_id
            ).filter(fuel_filter).select_related('aircraft').order_by('-session_date', '-id')
            
            # Combine all evaluations with their model type
            for eval_obj in evals_0_100:
                evaluations.append({
                    'evaluation': eval_obj,
                    'model_type': 'flightevaluation0_100',
                    'model_name': 'Evaluación 0-100'
                })
            
            for eval_obj in evals_100_120:
                evaluations.append({
                    'evaluation': eval_obj,
                    'model_type': 'flightevaluation100_120',
                    'model_name': 'Evaluación 100-120'
                })
            
            for eval_obj in evals_120_170:
                evaluations.append({
                    'evaluation': eval_obj,
                    'model_type': 'flightevaluation120_170',
                    'model_name': 'Evaluación 120-170'
                })
            
        except StudentProfile.DoesNotExist:
            pass
    
    context = {
        'search_form': search_form,
        'evaluations': evaluations,
        'student_profile': student_profile,
    }
    
    return render(request, 'transactions/add_fuel_transaction.html', context)


@login_required
@permission_required('accounts.can_manage_transactions')
def update_fuel_consumed(request):
    """Update fuel_consumed for a specific flight evaluation and create a StudentTransaction record."""
    student_id = None
    
    if request.method == 'POST':
        evaluation_id = request.POST.get('evaluation_id')
        model_type = request.POST.get('model_type')
        fuel_consumed = request.POST.get('fuel_consumed')
        
        if not all([evaluation_id, model_type, fuel_consumed]):
            messages.error(request, 'Faltan datos requeridos.')
            return redirect('transactions:add_fuel_transaction')
        
        try:
            fuel_consumed = Decimal(fuel_consumed)
            if fuel_consumed <= 0 or fuel_consumed > 1000:
                messages.error(request, 'El volumen de combustible debe estar entre 0.1 y 1000 litros.')
                return redirect('transactions:add_fuel_transaction')
            
            # Map model type to model class
            model_map = {
                'flightevaluation0_100': FlightEvaluation0_100,
                'flightevaluation100_120': FlightEvaluation100_120,
                'flightevaluation120_170': FlightEvaluation120_170,
            }
            
            model_class = model_map.get(model_type)
            if not model_class:
                messages.error(request, 'Tipo de evaluación inválido.')
                return redirect('transactions:add_fuel_transaction')
            
            # Get the evaluation
            evaluation = model_class.objects.get(pk=evaluation_id)
            student_id = evaluation.student_id  # Store for redirect
            
            # Check that fuel_consumed is currently 0.0
            if evaluation.fuel_consumed != Decimal('0.0') and evaluation.fuel_consumed != 0:
                messages.error(request, f'Esta evaluación ya tiene combustible especificado: {evaluation.fuel_consumed} litros.')
                return redirect('transactions:add_fuel_transaction')
            
            # Get student profile and aircraft
            student_profile = StudentProfile.objects.get(user__national_id=evaluation.student_id)
            aircraft = Aircraft.objects.get(registration=evaluation.aircraft.registration)
            fuel_cost = aircraft.fuel_cost
            
            # Calculate transaction amount
            transaction_amount = round(fuel_consumed * fuel_cost, 2)
            
            # Update the evaluation's fuel_consumed directly (bypassing save to avoid side effects)
            model_class.objects.filter(pk=evaluation_id).update(fuel_consumed=fuel_consumed)
            
            # Create StudentTransaction record
            # The save() method will automatically update the student balance since confirmed=True
            StudentTransaction.objects.create(
                student_profile=student_profile,
                amount=transaction_amount,
                type=StudentTransaction.DEBIT,
                category=StudentTransaction.FLIGHT,
                date_added=timezone.now().date(),
                added_by=request.user,
                confirmed=True,
                confirmed_by=request.user,
                confirmation_date=timezone.now(),
                notes=f'Combustible: {fuel_consumed}L - {aircraft.registration} - {evaluation.instructor_first_name} {evaluation.instructor_last_name}',
            )
            
            messages.success(request, f'Combustible actualizado exitosamente: {fuel_consumed} litros.')
            
        except (ValueError, TypeError):
            messages.error(request, 'El volumen de combustible debe ser un número válido.')
        except (FlightEvaluation0_100.DoesNotExist, FlightEvaluation100_120.DoesNotExist, FlightEvaluation120_170.DoesNotExist):
            messages.error(request, 'Evaluación no encontrada.')
        except StudentProfile.DoesNotExist:
            messages.error(request, 'Perfil de estudiante no encontrado.')
        except Exception as e:
            messages.error(request, f'Error al actualizar: {str(e)}')
    
    # Redirect back to search page, preserving student_id if available
    if student_id:
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(f"{reverse('transactions:add_fuel_transaction')}?student_id={student_id}")
    
    return redirect('transactions:add_fuel_transaction')