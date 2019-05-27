# Utilities for the home application
import json
import requests


osm_nominatim_base_url = 'https://nominatim.openstreetmap.org'
headers = {'User-Agent': 'Chaperone / Prototype v .01 (http://crymeclarity.com)'}


def get_osm_nominatim_search_results(query_string):
    osm_nominatim_url = osm_nominatim_base_url + '/search?q=' + query_string + '&format=json'
    response = requests.get(osm_nominatim_url, headers=headers)
    return json.loads(response.text)
