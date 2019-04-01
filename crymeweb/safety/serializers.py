from rest_framework import serializers

from .models import SafetyAnalysis


class SafetyAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyAnalysis
        fields = ('latitude', 'longitude', 'timestamp', 'model', 'estimate')