# forms.py
from django import forms
from .models import Device

class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['email', 'mac_address', 'serial_number']
