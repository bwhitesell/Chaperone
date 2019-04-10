from django.views import View
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from regions.models import GeometricRegion
from .forms import LatLonForm
from .serializers import SafetyAnalysisSerializer


#  API Views
class SafetyAnalysisAPIView(APIView):
    def post(self, request):
        serializer = SafetyAnalysisSerializer(data=request.data)
        lat = request.data.get('latitude')
        lon = request.data.get('longitude')

        if serializer.is_valid():
            if GeometricRegion.objects.in_domain(lon, lat):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response('lat/lon outside city limits of los angeles.', status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#  Good old-fashioned class-based views


class SafetyAnalysisView(View):
    def post(self, request):
        form = LatLonForm(request.POST)  # A form bound to the POST data
        print(form)
        print(form.data)
        if form.is_valid():
            print(form.cleaned_data['latitude'])
            print(form.cleaned_data['longitude'])

        return HttpResponse('hello world')
