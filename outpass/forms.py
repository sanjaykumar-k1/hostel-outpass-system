from django import forms
from .models import OutpassRequest


class OutpassRequestForm(forms.ModelForm):
    class Meta:
        model = OutpassRequest
        fields = ['reason', 'out_date', 'expected_return']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'out_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'expected_return': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }