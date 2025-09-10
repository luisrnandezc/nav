from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
from .models import StudentPayment
from .forms import StudentPaymentForm


@login_required
def payments_dashboard(request):
    """Payments Dashboard view showing latest 50 payments."""
    latest_payments = StudentPayment.objects.select_related(
        'student_profile__user', 
        'added_by', 
        'confirmed_by'
    ).all().order_by('-date_added')[:50]
    
    can_confirm_payments = (
        hasattr(request.user, 'staff_profile') and 
        request.user.staff_profile.can_confirm_payments
    )
    
    context = {
        'latest_payments': latest_payments,
        'can_confirm_payments': can_confirm_payments,
    }
    
    return render(request, 'payments/payments_dashboard.html', context)


@login_required
def confirm_payment(request, payment_id):
    """Confirm a payment - only for users with permission."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    if not (hasattr(request.user, 'staff_profile') and 
            request.user.staff_profile.can_confirm_payments):
        return JsonResponse({'success': False, 'error': 'No tiene permisos para confirmar pagos'})
    
    try:
        payment = get_object_or_404(StudentPayment, id=payment_id)
        
        if payment.confirmed:
            return JsonResponse({'success': False, 'error': 'El pago ya ha sido confirmado'})
        
        payment.confirm(request.user)
        
        return JsonResponse({
            'success': True, 
            'message': 'Pago confirmado exitosamente',
            'confirmed_by': f"{request.user.first_name} {request.user.last_name}",
            'confirmation_date': payment.confirmation_date.strftime('%d/%m/%Y %H:%M')
        })
        
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'An error occurred'})


@login_required
def unconfirm_payment(request, payment_id):
    """Unconfirm a payment - only for users with permission."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    if not (hasattr(request.user, 'staff_profile') and 
            request.user.staff_profile.can_confirm_payments):
        return JsonResponse({'success': False, 'error': 'No tiene permisos para desconfirmar pagos'})
    
    try:
        payment = get_object_or_404(StudentPayment, id=payment_id)
        
        if not payment.confirmed:
            return JsonResponse({'success': False, 'error': 'El pago no está confirmado'})
        
        payment.unconfirm()
        
        return JsonResponse({
            'success': True, 
            'message': 'Pago desconfirmado exitosamente'
        })
        
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'An error occurred'})


@login_required
def add_payment(request):
    """Add new payment form view."""
    if request.method == 'POST':
        cache_key = f"payment_rate_limit_{request.user.id}"
        payment_count = cache.get(cache_key, 0)
        
        if payment_count >= 10:
            messages.error(request, 'Has alcanzado el límite de pagos por hora. Intenta más tarde.')
            form = StudentPaymentForm(user=request.user)
            return render(request, 'payments/add_payment.html', {'form': form})
        
        form = StudentPaymentForm(request.POST, user=request.user)
        if form.is_valid():
            if request.user.role != 'STAFF':
                messages.error(request, 'Solo el personal autorizado puede agregar pagos.')
                return render(request, 'payments/add_payment.html', {'form': form})
            
            try:
                payment = form.save(commit=False)
                payment.added_by = request.user
                
                # If payment is being confirmed, set confirmed_by
                if payment.confirmed:
                    payment.confirmed_by = request.user
                    payment.confirmation_date = timezone.now()
                
                payment.save()
                
                cache.set(cache_key, payment_count + 1, 3600)
                
                return redirect('payments:payments_dashboard')
            except ValidationError as e:
                messages.error(request, f'Error al guardar el pago: {str(e)}')
                return render(request, 'payments/add_payment.html', {'form': form})
    else:
        form = StudentPaymentForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'payments/add_payment.html', context)