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
        if self.context.get('rt'):
            time_minutes = 60 * obj.timestamp.hour + obj.timestamp.minute
            ds = [[obj.longitude, obj.latitude, time_minutes, dow]]
        else:
            ds = [[obj.longitude, obj.latitude, 60 * hour, dow] for hour in range(0, 24)]

        ests = pc_model.predictor.predict_proba(np.array(ds))
        self.p_pos = ests[0][1] if self.context.get('rt') else ests[:,1]
        self.p_neg = ests[0][0] if self.context.get('rt') else ests[:,0]

        return {
            'positive_prob': self.p_pos,
            'negative_prob': self.p_neg,
        }

    def get_safety_rating(self, obj):
        if self.context.get('rt'):
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
        else:
            return 'N/A'

    def get_ref_id(self, obj):
        return hash(str(obj.id))
