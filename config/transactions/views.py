from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
from .models import StudentTransaction
from .forms import StudentTransactionForm


@login_required
def transactions_dashboard(request):
    """Transactions Dashboard view showing latest 50 transactions."""
    latest_transactions = StudentTransaction.objects.select_related(
        'student_profile__user', 
        'added_by', 
        'confirmed_by'
    ).all().order_by('-date_added')[:50]
    
    can_confirm_transactions = (
        hasattr(request.user, 'staff_profile') and 
        request.user.staff_profile.can_confirm_transactions
    )
    
    context = {
        'latest_transactions': latest_transactions,
        'can_confirm_transactions': can_confirm_transactions,
    }
    
    return render(request, 'transactions/transactions_dashboard.html', context)


@login_required
def confirm_transaction(request, transaction_id):
    """Confirm a transaction - only for users with permission."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    if not (hasattr(request.user, 'staff_profile') and 
            request.user.staff_profile.can_confirm_transactions):
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
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    if not (hasattr(request.user, 'staff_profile') and 
            request.user.staff_profile.can_confirm_transactions):
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
def add_transaction(request):
    """Add new transaction form view."""
    if request.method == 'POST':
        cache_key = f"transaction_rate_limit_{request.user.id}"
        transaction_count = cache.get(cache_key, 0)
        
        if transaction_count >= 10:
            messages.error(request, 'Has alcanzado el límite de transacciones por hora. Intenta más tarde.')
            form = StudentTransactionForm(user=request.user)
            return render(request, 'transactions/add_transaction.html', {'form': form})
        
        form = StudentTransactionForm(request.POST, user=request.user)
        if form.is_valid():
            if request.user.role != 'STAFF':
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