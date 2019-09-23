#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime

class KentikAPI:
  api_url = 'https://api.kentik.com/api/v5'

  kentik_headers = {
    'X-CH-Auth-Email': '',
    'X-CH-Auth-API-Token': '',
    'Content-Type': 'application/json'
  }

  def __init__(self, user, password):
    self.kentik_headers['X-CH-Auth-Email'] = user
    self.kentik_headers['X-CH-Auth-API-Token'] = password

  def call(self, **kwargs):
    url = self.api_url + kwargs['endpoint']
    response = requests.request(kwargs['method'], url, headers=self.kentik_headers, data=json.dumps(kwargs['payload']), allow_redirects=True, verify=True)
    r = None
    if response.status_code > 199 and response.status_code < 300:
      try:
        r = response.json()
      except ValueError:
        print ('ValueError')
        print(response.text)
      except JSONDecodeError:
        print ('JSONDecodeError')
        print(response.text)
    else:
      print(str(response.status_code) + ': ' + response.reason)
      print(response.text)
      print('*********** Request ***********')
      print(response.config)
    
    response.close()
    return r

  def topXQuery(self, query):
    return self.call(method="POST", endpoint="/query/topXdata", payload=query)