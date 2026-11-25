from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.models import Student
from .models import OutpassRequest
from .forms import OutpassRequestForm


@login_required
def request_outpass(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'No student profile found. Ask admin to create one.')
        return redirect('home')

    if request.method == 'POST':
        form = OutpassRequestForm(request.POST)
        if form.is_valid():
            outpass = form.save(commit=False)
            if outpass.expected_return <= outpass.out_date:
                form.add_error('expected_return', 'Return time must be after out time.')
            else:
                outpass.student = student
                outpass.save()
                messages.success(request, 'Outpass request submitted.')
                return redirect('my_requests')
    else:
        form = OutpassRequestForm()
    return render(request, 'outpass/request_form.html', {'form': form})


@login_required
def my_requests(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'No student profile found. Ask admin to create one.')
        return redirect('home')
    requests_list = OutpassRequest.objects.filter(student=student).order_by('-created_at')
    return render(request, 'outpass/my_requests.html', {'requests_list': requests_list})
