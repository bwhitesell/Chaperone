import numpy as np

from django.shortcuts import render

from classifiers.models import CrymeClassifier


models = CrymeClassifier.objects.load_models()


def dashboard_view(request):
    longitude = 34.059088
    latitude = -118.419385

    feature_vectors = np.array([[longitude, latitude, time] for time in range(0, 1440, 60)])

    # build charting data
    charting_data = {}
    for model in models:
        percentage_scaled_positive_prediction_vector = models[model].predict_proba(feature_vectors)[:, 1] * 100
        charting_data[model.target] = {
            'values': percentage_scaled_positive_prediction_vector.tolist(),
            'max': round(percentage_scaled_positive_prediction_vector.max(), 4) * 1.1
        }

    charting_data['max'] = max([charting_data[model_target]['max'] for model_target in charting_data])

    # build real-time risk estimates
    real_time_risk_ests = []
    for model in models:
        est_pos_prob, risk_rating = model.predict_rt_positive(longitude, latitude)
        real_time_risk_ests.append({
            'name': model.crime_name,
            'risk': round(est_pos_prob, 4) * 100,
            'rating': risk_rating
        })
    real_time_risk_ests = sorted(real_time_risk_ests, key=lambda k: k['risk'])


    context = {
        'charting_data': charting_data,
        'risk_ests': real_time_risk_ests,
    }

    return render(request, 'dashboard.html', context)

