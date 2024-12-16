from django.shortcuts import render, redirect
from .forms import FlightEvaluationForm

def submit_flight_evaluation(request):
    if request.method == 'POST':
        form = FlightEvaluationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard:dashboard')
    else:
        form = FlightEvaluationForm()
    
    return render(request, 'fms/flight_evaluation.html', {'form': form})