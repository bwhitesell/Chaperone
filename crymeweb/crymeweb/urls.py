from django.contrib import admin
from django.urls import path

from crime.views import crime_records_view
from classifiers.views import dashboard_view, health_view
from home.views import search_view, home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('crime-reports/<int:pg>', crime_records_view),
    path('', home_view, name='test'),
    path('search', search_view, name='search'),
    path('dashboard', dashboard_view, name='dashboard'),
    path('records/<int:pg>', crime_records_view, name='records'),
    path('model-health/<int:pk>', health_view, name='model-health'),
]

