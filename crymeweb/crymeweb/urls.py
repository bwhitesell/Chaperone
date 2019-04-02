from django.contrib import admin
from django.urls import path

from safety.views import SafetyAnalysisView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('safety-analysis/poc', SafetyAnalysisView.as_view())
]
