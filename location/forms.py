from django import forms
from .models import Test1
from django.utils import timezone
from django.utils.timezone import localtime

class Test1Form(forms.ModelForm):
    class Meta:
        model = Test1
        fields = ['date', 'location_in', 'location_out', 'in_time', 'range_12pm_user', 'range_3pm_user', 'out_time', 'stay_in_hrs', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'in_time': forms.TimeInput(attrs={'type': 'time'}),
            'range_12pm_user': forms.NumberInput(),
            'range_3pm_user': forms.NumberInput(),
            'out_time': forms.TimeInput(attrs={'type': 'time'}),
            'stay_in_hrs': forms.NumberInput(attrs={'step': '0.01'}),
            'status': forms.TextInput(attrs={'placeholder': 'Enter status here'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


                # Make specific fields optional
        self.fields['range_12pm_user'].required = False
        self.fields['range_3pm_user'].required = False
