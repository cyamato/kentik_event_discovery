#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime
from datetime import timedelta
import time
from random import randrange

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
    apiErrorCount = 0
    while True:
      response = requests.request(kwargs['method'], url, headers=self.kentik_headers, data=json.dumps(kwargs['payload']), allow_redirects=True, verify=True)
      r = None
      if response.status_code > 199 and response.status_code < 300:
        try:
          r = response.json()
          break 
        except ValueError:
          print ('ValueError')
          print(response.text)
        except JSONDecodeError:
          print ('JSONDecodeError')
          print(response.text)
      else:
        print ('*********** Kentik Request Error ' + str(apiErrorCount) + ' of 5 at ' + str(datetime.now()) + '***********')
        print (str(response.status_code) + ': ' + response.reason)
        with open('./kentikAPIErrorOut.json', 'w') as json_file:
          json_file.write(response.text)
        with open('./kentikAPIErrorIn.json', 'w') as json_file:
          json_file.write(json.dumps(kwargs['payload'], indent=2))
        print ('Check Error Log')
        print ()
      apiErrorCount = apiErrorCount + 1
      if apiErrorCount > 5:
        break
      randomWaitTime = randrange(1, 60, 1)
      print ('Waiting for ' + str(randomWaitTime) + ' seconds')
      endTime = time.time() + randomWaitTime
      while True:
        if time.time() < endTime:
          break
      response.close()
    response = None
    return r

  def topXQuery(self, query):
    return self.call(method="POST", endpoint="/query/topXdata", payload=query)