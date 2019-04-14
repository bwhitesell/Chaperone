from django.contrib import admin
from django.urls import path

from safety.views import SafetyAnalysisView, SafetyAnalysisAPIView, home_view, TodaysSafetyAnalysisAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/safety-analysis', SafetyAnalysisAPIView.as_view()),
    path('api/safety-analysis-today', TodaysSafetyAnalysisAPIView.as_view(), name='day_safety_analysis'),
    path('', home_view),
    path('safety-analysis', SafetyAnalysisView.as_view())
]

