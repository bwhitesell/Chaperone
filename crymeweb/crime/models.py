from django.db import models


class CrimeIncident(models.Model):

    _id = models.CharField(unique=True, max_length=100, null=False, blank=False)
    crime_desc = models.TextField()
    date_occ = models.DateField()
    time_occ = models.IntegerField()
    premis_desc = models.TextField()
    longitude = models.FloatField()
    latitude = models.FloatField()
