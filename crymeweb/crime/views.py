import json
from django.shortcuts import render
from django.core.paginator import Paginator

from .models import CrimeIncident, DailyCrimeVolume


def crime_records_view(request, pg):
    # crime-records table processing
    crime_records = CrimeIncident.objects.all().order_by('-date_occ_str')
    paginator = Paginator(crime_records, 15)
    viewable_reports = paginator.get_page(pg)

    # crime-volume line chart processing
    daily_crime_vol = DailyCrimeVolume.objects.all().order_by('date_occ_str').values_list(
        'volume', 'date_occ_str'
    )
    daily_vols = [itm[0] for itm in daily_crime_vol]
    daily_labels = [itm[1].split(' ')[0] for itm in daily_crime_vol]

    context = {
        'crime_reports': viewable_reports,
        'daily_crime_vol_data': daily_vols,
        'daily_crime_vol_labels': daily_labels,
        'max_chart_val': int(max(daily_vols)),

    }
    return render(request, 'records.html', context=context)

