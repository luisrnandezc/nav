from django.shortcuts import render, redirect
from .forms import FlightEvaluationForm

def submit_flight_evaluation(request):
    if request.method == 'POST':
        form = FlightEvaluationForm(request.POST, user=request.user)
        if form.is_valid():
            # form.save()
            print(form.cleaned_data) # This is for debug purposes.
            return redirect('dashboard:dashboard')
    else:  
        form = FlightEvaluationForm(user=request.user)
    
    return render(request, 'fms/flight_evaluation.html', {'form': form})