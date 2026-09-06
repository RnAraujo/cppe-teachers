from django import forms
from .models import Teacher, Contribution

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['dni', 'first_name', 'last_name', 'registration_code', 'is_enabled', 'photo']
        widgets = {
            'dni': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'registration_code': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'h-5 w-5'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'w-full'}),
        }

class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['month', 'year', 'comments', 'observations']
        widgets = {
            'month': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'year': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded'}),
            'comments': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 2}),
            'observations': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 2}),
        }