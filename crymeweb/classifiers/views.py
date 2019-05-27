import numpy as np

from django.shortcuts import render
from django.http import HttpResponseBadRequest, Http404

from crime.models import CrimeIncident
from regions.models import GeometricRegion
from .models import CrymeClassifier
from .utils import build_view_box, lat_delta, lon_delta


models = CrymeClassifier.objects.load_models()


def dashboard_view(request):

    longitude = request.GET.get('lon')
    latitude = request.GET.get('lat')
    name = request.GET.get('name')

    if not name:
        name = str(longitude) + ', ' + str(latitude)

    if (not longitude) or (not latitude):
        raise Http404

    # check lon/lat
    try:
        longitude = float(longitude)
        latitude = float(latitude)
    except:
        return HttpResponseBadRequest(content='Invalid Lat/Lon specified.')

    if not GeometricRegion.objects.in_domain(longitude, latitude):
        return HttpResponseBadRequest(content="We don't think location is within the city limits of los angeles. :/")

    feature_vectors = np.array([[longitude, latitude, time] for time in range(0, 1440, 60)])

    # get recent crimes nearby
    nearby_crimes = CrimeIncident.objects.filter(
        lat__lte=latitude + lat_delta,
        lat__gte=latitude - lat_delta,
        lon__lte=longitude + lat_delta,
        lon__gte=longitude - lat_delta,
    )

    # build real-time risk estimates
    real_time_risk_ests = []
    for model in models:
        percentage_scaled_positive_prediction_vector = models[model].predict_proba(feature_vectors)[:, 1] * 100
        est_pos_prob, risk_rating = model.predict_rt_positive(longitude, latitude)
        real_time_risk_ests.append({
            'name': model.crime_name,
            '24_hr_risk': percentage_scaled_positive_prediction_vector.tolist(),
            '24_hr_max': round(percentage_scaled_positive_prediction_vector.max() * 1.1, 2),
            'risk': round(est_pos_prob * 100, 2),
            'rating': risk_rating,
        })
        y_axis_max = max([model['24_hr_max'] for model in real_time_risk_ests])

    real_time_risk_ests = sorted(real_time_risk_ests, key=lambda k: k['risk'], reverse=True)

    context = {
        'real_time_risk_ests': real_time_risk_ests,
        'risk_ests_row_1': real_time_risk_ests[:4],
        'risk_ests_row_2': real_time_risk_ests[4:8],
        'view_box': build_view_box(longitude, latitude),
        'nearby_crimes': nearby_crimes,
        'name': name,
        'y_axis_max': y_axis_max,
    }
    return render(request, 'dashboard.html', context)

