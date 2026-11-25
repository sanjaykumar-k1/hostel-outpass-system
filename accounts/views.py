from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def get_role(user):
    if user.is_superuser or user.groups.filter(name='Warden').exists():
        return 'Warden'
    if user.groups.filter(name='Security').exists():
        return 'Security'
    return 'Student'


@login_required
def home(request):
    role = get_role(request.user)
    return render(request, 'accounts/dashboard.html', {'role': role})
