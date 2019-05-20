from django.contrib import admin
from django.urls import path

from crime.views import crime_records_view, test_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('crime-reports/<int:pg>', crime_records_view),
    path('', test_view),
]

