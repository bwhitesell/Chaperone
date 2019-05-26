import pickle as p
from django.db import models


class CrymeClassifierManager(models.Manager):

    def load_models(self):
        active_models = self.filter(active=True)
        return {model.target: model.load_model() for model in active_models}


class CrymeClassifier(models.Model):
    name = models.CharField(max_length=20, null=False, blank=False)
    file_path = models.TextField(null=False, blank=False)
    target = models.CharField(max_length=10, null=False, blank=False)
    active = models.BooleanField(default=False)

    risk_rating_low = models.FloatField()
    risk_rating_medium = models.FloatField()
    risk_rating_high = models.FloatField()
    risk_rating_very_high = models.FloatField()

    objects = CrymeClassifierManager()

    def __str__(self):
        return self.name

    def load_model(self):
        try:
            return p.load(open(self.file_path, 'rb'))
        except FileNotFoundError:
            return None
