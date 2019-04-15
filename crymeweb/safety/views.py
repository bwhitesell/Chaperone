
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views import View
import geocoder
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from regions.models import GeometricRegion
from .forms import LatLonForm
from .serializers import SafetyAnalysisSerializer
from .utils import get_client_ip


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
                HttpResponseBadRequest('Invalid query string.')
            if GeometricRegion.objects.in_domain(float(lon), float(lat)):
                return render(request, 'security/analysisPage.html', context={'lat': lat, 'lon': lon})
            else:
                return HttpResponseBadRequest('lat/lon outside city limits of los angeles.')

        return HttpResponseBadRequest('Please provide lat/lon query parameters.')

    def post(self, request):
        form = LatLonForm(request.POST)
        print(form)
        print(form.data)
        if form.is_valid():
            lat = form.cleaned_data['latitude']
            lon = form.cleaned_data['longitude']
            return redirect('/safety-analysis?lat=' + str(lat) + '&lon=' + str(lon))
        return HttpResponseBadRequest('Please provide lat/lon parameters.')


def home_view(request):
    geo = geocoder.ip(get_client_ip(request)).latlng
    geo = {'longitude': geo[0], 'latitude': geo[1]}
    return render(request, 'index.html', geo)
