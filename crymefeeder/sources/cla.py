import json
import requests

from settings import REQUEST_TIMEOUT_LIMIT


class CLAAPIError(Exception):
    def __init__(self, **kwargs):
        self.url = kwargs.get('url')
        self.code = kwargs.get('code')
        self.msg = kwargs.get('msg')

    def __str__(self):
        return self.msg + f'\n details: \n url: {self.url} \n code: {self.code}'


class CLAAPI:
    timeout = REQUEST_TIMEOUT_LIMIT
    token = None
    headers = None
    base_url = 'https://data.lacity.org/resource/63jg-8b9z.json?$select=:*, *&$order=:id'

    def __init__(self, token):
        self.token = token
        self.headers = {'X-App-Token': self.token}

    def _construct_url_arg(self, **kwargs):
        url = self.base_url
        for arg, value in kwargs.items():
            url += '&$' + str(arg) + '=' + str(value)
        return url

    def _request(self, url, **headers):
        heads = self.headers.update(headers)
        response = requests.get(url, headers=heads, timeout=self.timeout)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            err_info = {
                'url': url,
                'code': response.status_code,
                'msg': 'Unhandled status code received from server.'
            }
            raise CLAAPIError(**err_info)

    def get_incidents(self, limit=1000, offset=0):
        query_args = {
            'limit': limit,
            'offset': offset
        }
        return self._request(self._construct_url_arg(**query_args))

    def get_incident(self, row_id):
        query_args = {
            'where': ':id=' + "'" + row_id + "'"
        }
        return self._request(self._construct_url_arg(**query_args))

    def get_incidents_created_after(self, dt, limit=1000, offset=0):
        query_args = {
            'where': ':created_at>' + "'" + str(dt).replace(' ', 'T') + "'",
            'limit': limit,
            'offset': offset
        }
        return self._request(self._construct_url_arg(**query_args))

    def get_all_incidents(self, batch_size=50000):
        results_chunk = True
        results = []
        page = 0

        while results_chunk:
            print(page)
            results_chunk = self.get_incidents(limit=batch_size, offset=batch_size * page)
            results += results_chunk
            page += 1

        return results
