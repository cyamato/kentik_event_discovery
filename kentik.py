#!/usr/bin/python3
# -*- coding: utf-8 -*-
import requests
from datetime import datetime

class KentikAPI:
  api_url = 'https://api.kentik.com/api/v5/'

  endpoints = {
    "query": {
      "topx": {
        "data": kentik_api_url + 'query/topXdata'
      }
    }
  }

  headers = {
    'X-CH-Auth-Email': '',
    'X-CH-Auth-API-Token': '',
    'Content-Type': 'application/json'
  }

  def __init__(self, user, password):
    self.kentik_headers['X-CH-Auth-Email'] = user
    self.kentik_headers['X-CH-Auth-API-Token'] = password

  def call(self, **kwargs):
    response = requests.request(kwargs.method, kwargs.url, headers = self.headers, data = kwargs.payload, allow_redirects=True, verify=False)
    return response.json()
