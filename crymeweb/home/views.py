from django.shortcuts import render
from django.http import HttpResponse

from .utils import get_osm_nominatim_search_results


def home_view(request):
    return render(request, 'home.html')


def search_view(request):
    search_query = request.GET.get('query').replace(' ', '/')
    search_results = get_osm_nominatim_search_results(search_query)[:5]
    if not search_results:
        search_results = []
    return render(request, 'search.html', context={'search_results': search_results})
