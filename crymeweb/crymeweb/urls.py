from django.contrib import admin
from django.views.generic import TemplateView
from django.urls import path

from safety.views import SafetyAnalysisView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/safety-analysis', SafetyAnalysisView.as_view()),
    path('', TemplateView.as_view(template_name='home.html'),)
]
