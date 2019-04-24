from datetime import datetime, timedelta
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views import View
import geocoder
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from regions.models import GeometricRegion
from utils import SafeMongoClientWrapper
from .forms import LatLonForm
from .serializers import SafetyAnalysisSerializer
from .utils import get_client_ip, qt_mile_lat, qt_mile_lon


mc = SafeMongoClientWrapper(settings.DB_URL, settings.DB_NAME)


#  API Views
class SafetyAnalysisAPIView(APIView):
    def post(self, request):
        serializer = SafetyAnalysisSerializer(data=request.data, context={'rt': True})

        if serializer.is_valid():
            if GeometricRegion.objects.in_domain(
                    serializer.validated_data['longitude'],
                    serializer.validated_data['latitude']
            ):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response('lat/lon outside city limits of los angeles.', status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TodaysSafetyAnalysisAPIView(APIView):
    def post(self, request):
        serializer = SafetyAnalysisSerializer(data=request.data)

        if serializer.is_valid():
            if GeometricRegion.objects.in_domain(
                    serializer.validated_data['longitude'],
                    serializer.validated_data['latitude']
            ):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response('lat/lon outside city limits of los angeles.', status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#  Good old-fashioned templates
class SafetyAnalysisView(View):
    def get(self, request):
        lat = request.GET.get('lat', None)
        lon = request.GET.get('lon', None)
        if lat and lon:
            try:
                lat = float(lat)
                lon = float(lon)
            except ValueError:
                return HttpResponseBadRequest('Invalid query string.')
            if GeometricRegion.objects.in_domain(float(lon), float(lat)):
                crime_search_query = {
                    'location_1.coordinates.0': {'$gt': lat - qt_mile_lat},
                    'location_1.coordinates.0': {'$lt': lat + qt_mile_lat},
                    'location_1.coordinates.1': {'$gt': lon - qt_mile_lon},
                    'location_1.coordinates.1': {'$lt': lon + qt_mile_lon},
                    'date_occ': {'$gt': str(datetime.now() - timedelta(days=7)).replace(' ', 'T')}

                 }
                crimes = list(mc.execute('incidents', 'find', crime_search_query).limit(10))

                return render(request, 'security/analysisPage.html', context={'lat': lat, 'lon': lon, 'crimes': crimes})
            else:
                return HttpResponseBadRequest('lat/lon outside city limits of los angeles.')

        return HttpResponseBadRequest('Please provide lat/lon query parameters.')

    def post(self, request):
        form = LatLonForm(request.POST)
        if form.is_valid():
            lat = form.cleaned_data['latitude']
            lon = form.cleaned_data['longitude']
            return redirect('/safety-analysis?lat=' + str(lat) + '&lon=' + str(lon))
        return HttpResponseBadRequest('Please provide lat/lon parameters.')


def home_view(request):
    # ip = get_client_ip(request)
    ip = '161.149.146.201'
    geo = geocoder.ip(ip).latlng
    geo = {'longitude': geo[0], 'latitude': geo[1]}
    return render(request, 'index.html', geo)
