import datetime
import json
import requests
import settings


class CLABackendError(Exception):
    def __init__(self, **kwargs):
        self.url = kwargs.get('url')
        self.code = kwargs.get('code')
        self.reason = kwargs.get('reason')


class CLABackend:
    timeout = 30
    token = None
    headers = None
    base_url = 'https://data.lacity.org/resource/7fvc-faax.json'

    def __init__(self, token=settings.SOCRATA_APP_TOKEN):
        self.token = token
        self.headers = {'X-App-Token': self.token}

    def _request(self, url, **headers):
        heads = self.headers.update(headers)
        response = requests.get(url, headers=heads, timeout=self.timeout)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            raise CLABackendError(
                **{'url': url,
                   'code': response.status_code,
                   'reason': 'Invalid status code rec. from server.'}
            )

    def get_crime_incidents(self, limit=1000, offset=0):
        rl = self.base_url + '?' + 'select=:*, *' + '&' +\
             '$limit=' + str(limit) + '&' + '$offset=' + str(offset)
        print(rl)
        return self._request(rl)


if __name__ == '__main__':
    be = CLABackend()
    l = be.get_data(limit=50000)
    print(len(l))


