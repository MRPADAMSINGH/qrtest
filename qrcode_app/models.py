# models.py
from django.db import models

class Device(models.Model):
    email = models.EmailField()
    mac_address = models.CharField(max_length=17, unique=True)  # Assuming MAC address is in standard format
    serial_number = models.CharField(max_length=50, unique=True)  # Adjust max_length as needed

    def __str__(self):
        return f"{self.email} - {self.mac_address} - {self.serial_number}"
