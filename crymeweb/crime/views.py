from django.shortcuts import render
from django.core.paginator import Paginator

from .models import CrimeIncident, DailyCrimeVolume, CrimesPremisesVolume


def crime_records_view(request, pg):
    qs = CrimeIncident.objects.all().order_by('-date_occ_str')

    paginator = Paginator(CrimeIncident.objects.all().order_by('-date_occ_str'), 20)
    crime_reports = paginator.get_page(pg)
    daily_volume_dates, daily_volume_volumes = DailyCrimeVolume.objects.get_chart_data()
    crime_prem_descriptions, crime_prem_volumes = CrimesPremisesVolume.objects.get_chart_data()

    context = {
        'reports': crime_reports,
        'dates': daily_volume_dates,
        'date_volumes': daily_volume_volumes,
        'premises': crime_prem_descriptions,
        'prem_volumes': crime_prem_volumes
    }
    return render(request, 'crime/crimeReports.html', context=context)


def test_view(request):
    return render(request, 'crime/crimeByPremisesChart.html')