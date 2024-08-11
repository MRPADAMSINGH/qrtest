from django.db import models

class Test1(models.Model):
    date = models.DateField()
    location_in = models.CharField(max_length=255)
    location_out = models.CharField(max_length=255)
    in_time = models.TimeField()
    range_12pm_user = models.CharField(max_length=255)
    range_3pm_user = models.CharField(max_length=255)
    out_time = models.TimeField()
    stay_in_hrs = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=50)

    def __str__(self):
        return f"Record for {self.date} - {self.location_in} to {self.location_out}"
