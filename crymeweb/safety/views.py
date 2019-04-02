from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from regions.models import GeometricRegion
from .serializers import SafetyAnalysisSerializer


class SafetyAnalysisView(APIView):
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
