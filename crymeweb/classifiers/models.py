import numpy as np
import pickle as p

from django.db import models
from django.utils import timezone

from .utils import datetime_to_minutes_into_day


class CrymeClassifierManager(models.Manager):

    def load_models(self):
        active_models = self.filter(active=True)
        return {model: model.clf for model in active_models}


class CrymeClassifier(models.Model):
    name = models.CharField(max_length=20, null=False, blank=False)
    file_path = models.TextField(null=False, blank=False)
    target = models.CharField(max_length=10, null=False, blank=False)
    active = models.BooleanField(default=False)
    crime_name = models.CharField(max_length=50)

    risk_rating_low = models.FloatField()
    risk_rating_medium = models.FloatField()
    risk_rating_high = models.FloatField()
    risk_rating_very_high = models.FloatField()

    objects = CrymeClassifierManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_model()

    def __str__(self):
        return self.crime_name + ' Classifier'

    def load_model(self):
        try:
            self.clf = p.load(open(self.file_path, 'rb'))
        except FileNotFoundError:
            self.clf = None

    def predict_rt_positive(self, lon, lat):
        now = timezone.now()
        est_pos_prob = self.clf.predict_proba(
            np.array([[lon, lat, datetime_to_minutes_into_day(now)]])
        )[0][1]
        return est_pos_prob, self.get_risk_rating(est_pos_prob)

    def get_risk_rating(self, positive_prob_est):
        if positive_prob_est <= self.risk_rating_low:
            return 'Low'
        elif self.risk_rating_low < positive_prob_est <= self.risk_rating_medium:
            return 'Average'
        elif self.risk_rating_medium < positive_prob_est <= self.risk_rating_high:
            return 'Elevated'
        elif self.risk_rating_high < positive_prob_est:
            return 'High'
