#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import os
import sys
import json
import re
import math
import copy
from datetime import datetime
from datetime import timedelta
import hashlib
import base64

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import requests

# from memory_profiler import profile

import kentik
import baseline

def args():
  """
  Get command line arguments
  """
  parser = argparse.ArgumentParser(description='Find and plot past events from Kentik data')
  parser.add_argument('--start', dest='queryStartTime', default='2019-08-22 00:00', help='A Datetime string in the form of 2019-08-22 00:00')
  parser.add_argument('--end', dest='queryEndTime', default='2019-09-22 00:00', help='A Datetime string in the form of 2019-09-22 00:00')
  parser.add_argument('--resultion', dest='queryResultion', choices=[1,5,10,60], default=1, help='The time rounding in minutes that should be targeted for Kentik Query Results')
  parser.add_argument('--dbUrl', dest='harperDBUrl', default=None, help='The URL for the HarperDB instance to use if desired')
  parser.add_argument('--dbUser', dest='harperDBUser', default=None, help='The URL for the HarperDB instance to use if desired')
  parser.add_argument('--dbPassword', dest='harperDBPassword', default=None, help='The URL for the HarperDB instance to use if desired')
  args = parser.parse_args()
  
  harperDBUrl = None
  harperDB_Auth = None
  
  if args.harperDBUrl and args.harperDBUser and args.harperDBPassword:
    harperDBUrl = args.harperDBUrl
    harperDB_Auth = args.harperDBUser + ':' + args.harperDBPassword
    harperDB_Auth = base64.b64encode(harperDB_Auth.encode("utf-8"))
    harperDB_Auth = "Basic " + str(harperDB_Auth, "utf-8")
  if os.environ.get('HARPERDB_URL', None) and os.environ.get('HARPERDB_USER', None) and os.environ.get('HARPERDB_PASSWORD', None):
    print ('Loading HarperDB Info')
    harperDBUrl = os.environ['HARPERDB_URL']
    harperDBUser = os.environ['HARPERDB_USER']
    harperDBPassword = os.environ['HARPERDB_PASSWORD']
    harperDB_Auth = harperDBUser + ':' + harperDBPassword
    harperDB_Auth = base64.b64encode(harperDB_Auth.encode("utf-8"))
    harperDB_Auth = "Basic " + str(harperDB_Auth, "utf-8")
    
  return args, harperDBUrl, harperDB_Auth

def getDBData():
  headers = {
    'Content-Type': 'application/json',
    'Authorization': harperDB_Auth
  }
  payload = {
    "operation":"search_by_value",
    "schema": "kentik",
    "table": "kentikhistory",
    "hash_attribute": "name",
    "search_attribute": "name",
    "search_value":['*'],
    "get_attributes":['*']
  }
  response = requests.request('POST', harperDBUrl, headers=headers, data=json.dumps(payload), allow_redirects=False)
  r = response.json()
  response = None
  return r

if not os.path.exists('./output'):
  os.makedirs('./output')

print ('Setting up arguments')
arguments, harperDBUrl, harperDB_Auth = args()

tsData = getDBData()
for rec in tsData:
  print ('DB Collected: ' + rec['name'] + ' ' + str(len(rec['timeSeries'])))

# print ('Making Baselines')
# base = baseline.Baselines()
# firstBase = base.build_roll_up(3600, 95, tsData) # Find p95 per hour
# # Example: For the p95% for the same hour of the same day of the week using hourly roll ups as the input "build_baseline(168, 95. rollup)"
# # nth [int]: The nth element to be in each array = Logicly this also means the number of arrays :) too
# # pTarget [int]: The pN% target; 95 = p95%
# baseline = base.build_baseline(168, 95, firstBase)

# print ('Checking for events')
# # base.get_alerts(alertWindowSize, alertSameWindow, eventsPerAlert, eventWindowSize, eventMesurment, baselineStartIndex, baselineWindow, aboveBase, metricType, baselines, ts)
# # 2 events within 10mins and every event with in 10mins is an alert where an event is a any mesurement with in 1min over 100% of the baseline using tsData as the input ts data
# alerts = base.get_alerts(600, 600, 2, 120, 95, 0, 3600, 100, 'precent', baseline, tsData)

# # Filter to only report clients with attacks
# print ('Just Atacks')
# print ()
# atacks = []
# for atack in alerts:
#   if len(atack['alerts']) > 0:
#     atacks.append(atack.copy())
# baseline = None
# tsData = None
# alerts = None
# atack = None
# print (str(len(atacks)) + ' Atacks Fond')
# print ()

# print ('Writing to csv')
# with open('./output/kentik_historic_events.csv', 'w') as csv_file:
#   csv_file.write('CustomerASN, StartTime, EndTime, Length, Value, Baseline, Metric\n')
#   for customer in atacks:
#     for atack in customer['alerts']:
#       csv_file.write('"' + customer['name'] + '",' + str(int(atack['start']/1000)) + ',' +  str(int(atack['end']/1000)) + ',' +  str(atack['length']) + ',' +  str(atack['value']) + ',' + str(atack['baseline']) + ',' + customer['metric'] + '\n')
#   csv_file.close()
# atacks = None
# print ('Alerts wrtien too ./output/kentik_historic_events.csv')

# print ('Making Graph')
# atackDS = pd.read_csv('./output/kentik_historic_events.csv', parse_dates='StartTime', skiprows=0)
# print (atackDS)

# sns.set(style='whitegrid')
# sns.set_context('poster')
# f, ax = plt.subplots(figsize=(6.5, 6.5))
# sns.despine(f, left=True, bottom=True)
# kah = sns.scatterplot(x='StartTime', y='Value',
#                 hue='CustomerASN', size='Length',
#                 palette='Blues_d',
#                 sizes=(1, 8), linewidth=0,
#                 data=atackDS, ax=ax)
# print ('Saving Graph Image to ./output/kentik_historic_events.png')
# plt.savefig('./output/kentik_historic_events.png')
# print ('Showing Graph Image')
# plt.show()