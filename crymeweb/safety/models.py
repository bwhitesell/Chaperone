from django.db import models


class SafetyModel(models.Model):
    MODEL_TYPES = (('PC', 'estimated_time_proximity_incidents'),)

    name = models.CharField(max_length=100)
    version = models.CharField(max_length=100)
    pred_type = models.CharField(max_length=2, choices=MODEL_TYPES)
    notes = models.TextField(blank=True)
    publish_timestamp = models.DateTimeField()

    current = models.BooleanField(blank=False)


class SafetyAnalysisRequest(models.Model):
    latitude = models.FloatField(null=False, blank=False)
    longitude = models.FloatField(null=False, blank=False)
    timestamp = models.DateTimeField(null=False, blank=False)

    model = models.ForeignKey(SafetyModel, blank=True, null=True, on_delete=models.CASCADE)
    estimate = models.FloatField(blank=True, null=True)

