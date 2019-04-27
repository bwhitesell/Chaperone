from datetime import datetime
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
import numpy as np
import pickle as p


class SafetyModelManager(models.Manager):
    def active_model(self, model_type):
        try:
            return self.get(pred_type=model_type, current=True)
        except ObjectDoesNotExist:
            return None


class SafetyModel(models.Model):
    predictor = None

    MODEL_TYPES = (('PC', 'estimated_time_proximity_incidents'),)

    name = models.CharField(max_length=100)
    version = models.CharField(max_length=100)
    pred_type = models.CharField(max_length=2, choices=MODEL_TYPES)
    notes = models.TextField(blank=True)
    publish_timestamp = models.DateTimeField()

    current = models.BooleanField(blank=False)

    objects = SafetyModelManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_predictor()

    def __str__(self):
        return 'Model: ' + self.name

    def load_predictor(self):
        self.predictor = p.load(open(settings.BINARIES_DIR + self.name + '.p', 'rb'))


class SafetyAnalysis(models.Model):
    latitude = models.FloatField(null=False, blank=False)
    longitude = models.FloatField(null=False, blank=False)
    timestamp = models.DateTimeField(null=False, blank=False)


class SyntheticAnalysisRequest(models.Model):
    latitude = models.FloatField(null=False, blank=False)
    longitude = models.FloatField(null=False, blank=False)
    timestamp = models.DateTimeField(null=False, blank=False)

    model = models.ForeignKey(SafetyModel, blank=True, null=True, on_delete=models.CASCADE)
    estimate = models.FloatField(blank=True, null=True)

