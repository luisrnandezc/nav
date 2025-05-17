from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import FlightEvaluationForm

@login_required
def submit_flight_evaluation(request):
    """Handle flight evaluation form submission."""
    if request.method == 'POST':
        form = FlightEvaluationForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                form.save()  # This will save both FlightEvaluation and FlightLog
                return redirect('dashboard:dashboard')
            except Exception as e:
                messages.error(request, f'Error al guardar la evaluación: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:  
        form = FlightEvaluationForm(user=request.user)

    return render(request, 'fms/flight_evaluation.html', {'form': form})