from rest_framework import serializers
import numpy as np
from .models import SafetyAnalysis
from .utils import pc_model, PC_DESCRIPTION


class SafetyAnalysisSerializer(serializers.ModelSerializer):
    ref_id = serializers.SerializerMethodField()
    estimate = serializers.SerializerMethodField()
    safety_rating = serializers.SerializerMethodField()

    class Meta:
        model = SafetyAnalysis
        fields = ('ref_id', 'latitude', 'longitude', 'timestamp', 'estimate', 'safety_rating')

    p_pos = None
    p_neg = None

    def get_estimate(self, obj):
        dow = obj.timestamp.weekday()
        time_minutes = 60 * obj.timestamp.hour + obj.timestamp.minute
        self.p_neg, self.p_pos = pc_model.predictor.predict_proba(
            np.array([[obj.longitude, obj.latitude, time_minutes, dow]])
        )[0]
        return {
            'positive_prob': self.p_pos,
            'negative_prob': self.p_neg,
            'description': PC_DESCRIPTION,
        }

    def get_safety_rating(self, obj):
        if self.p_pos < .03:
            return 'Very Safe'

        if .06 > self.p_pos >= .03:
            return 'Safe'

        if .09 > self.p_pos >= .06:
            return 'Neutral'

        if .12 > self.p_pos >= .09:
            return 'Somewhat Dangerous'

        if self.p_pos >= .12:
            return 'Dangerous'

    def get_ref_id(self, obj):
        return hash(str(obj.id))
