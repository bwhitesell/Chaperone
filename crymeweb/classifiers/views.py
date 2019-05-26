import numpy as np

from django.shortcuts import render

from classifiers.models import CrymeClassifier


models = CrymeClassifier.objects.load_models()


def dashboard_view(request):
    longitude = 34.059088
    latitude = -118.419385

    feature_vectors = np.array([[longitude, latitude, time] for time in range(0, 1440, 60)])

    risk_estimates = {}
    for model in models:
        risk_estimates[model] = models[model].predict_proba(feature_vectors)[:,1].tolist()

    context = {}
    context['risk_chart_values'] = risk_estimates

    return render(request, 'dashboard.html', context)
