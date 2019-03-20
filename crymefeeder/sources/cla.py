import datetime
import json
import requests
import settings


class CLAAPIError(Exception):
    def __init__(self, **kwargs):
        self.url = kwargs.get('url')
        self.code = kwargs.get('code')
        self.msg = kwargs.get('msg')

    def __str__(self):
        return self.msg + f'\n details: \n url: {self.url} \n code: {self.code}'


class CLAAPI:
    timeout = 30
    token = None
    headers = None
    base_url = 'https://data.lacity.org/resource/7fvc-faax.json?$select=:*, *'

    def __init__(self, token=settings.SOCRATA_APP_TOKEN):
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
            raise CLABackendError(**err_info)

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

    def get_incidents_created_after(self, dt):
        query_args = {
            'created_at': '> ' + str(dt).replace(' ', 'T')
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


if __name__ == '__main__':
    be = CLABackend()
    l = be.get_data(limit=50000)
    print(len(l))


