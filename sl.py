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

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

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
  args = parser.parse_args()
  return args
  
def setupKentikAPI():
  # Setup API
  if not os.environ.get('KENTIK_API_USER', None):
    print ('Enviroment Var KENTIK_API_USER must be set')
    sys.exit()
  if not os.environ.get('KENTIK_API_PASSWORD', None):
    print ('Enviroment Var KENTIK_API_PASSWORD must be set')
    sys.exit()
    
  return kentik.KentikAPI(os.environ['KENTIK_API_USER'], os.environ['KENTIK_API_PASSWORD'])

def getCustomers(queryStartTime, queryEndTime):
  """
  Function to run a query on Kentik for all customer
  queryStartTime [string]: the time date to start the query
  queryEndTime [string]: the time date to end the query
  """
  # Load query
  with open('kentik_query_customers.json') as json_file:
    customerQuery = json.load(json_file)
  customerQuery['queries'][0]['query']['starting_time'] = queryStartTime
  customerQuery['queries'][0]['query']['ending_time'] = queryEndTime
  
  # Run Query
  customers = kAPI.topXQuery(customerQuery)
  
  # Get ASNs from results ASN should be the last thing in the key
  customerList = []
  for result in customers['results'][0]['data']:
    asnRegEx = re.compile('\((\d*)\)$')
    asn = asnRegEx.search(result['key'])
    customerList.append(asn.group(1))
  
  return customerList

def getTimeSlices(start, end, targetResultion):
  if targetResultion == 1: targetResultion = 3 * 60    # < 3h	Full	1 minute
  if targetResultion == 5: targetResultion = 24 * 60   # >= 3h and < 24h	Full	5 minute
  if targetResultion == 10: targetResultion = 72 * 60  # >= 24h and < 3 days	Full	10 minute
  if targetResultion == 60: targetResultion = 0        # > 3 days	Fast	60 minute
  
  start = datetime.strptime(start, '%Y-%m-%d %H:%M')
  end = datetime.strptime(end, '%Y-%m-%d %H:%M')
  totalQueryMins = (end-start).total_seconds()/60
  
  timeSlices = [] # An array to hold time slice object
  startTime = start
  slices = math.floor(totalQueryMins / targetResultion)
  if slices == 0: slices = slices + 1
  for i in range(slices):
    endTime = startTime + timedelta(minutes=targetResultion)
    if endTime > end:
      endTime = end
    timeSlices.append({
      'start': startTime.strftime('%Y-%m-%d %H:%M'),
      'end': (endTime - timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M')
    })
    startTime = endTime
  
  return timeSlices

def groupCustomers(customers):
  """
  This function will group customers in to groups of 40
  customers [array]: An array of customers
  """
  groups = []
  totalCustomers = len(customers) - 1
  startIndex = 0
  endIndex = 39
  
  while endIndex < totalCustomers:
    print('start: ' + str(startIndex) + " - end: " + str(endIndex))
    groups.append(customers[startIndex:endIndex])
    startIndex = endIndex + 1
    endIndex = endIndex + 40
  
  # Group any hanging ones
  if endIndex > totalCustomers and startIndex < totalCustomers:
    endIndex = totalCustomers
    print('start: ' + str(startIndex) + " - end: " + str(endIndex))
    groups.append(customers[startIndex:endIndex])
    
  return groups

def getTSData(customerGroups, slices):
  """
  This function will make looped bulk API Calls to Kentik
  """
  # Load query
  with open('kentik_query_tsData.json') as json_file:
    tsBulkQueryBase = json.load(json_file)
    
  combinedTSData = [] # An empty array to hold complied results
  
  # Loop through each group of customers
  workingGroup = 0 # Only used for tracking in the print output
  for cGroup in customerGroups:
    workingGroup = workingGroup + 1
    
    # Loop throguh and build bulk queries over time for each group
    for tsSlice in slices:
      # Setup Query
      tsBulkQuery = copy.deepcopy(tsBulkQueryBase)
      if len(tsBulkQuery['queries'][0]['query']['filters_obj']['filterGroups']) < 1:
        tsQuery['query']['filters_obj']['filterGroups'] = [{              
          'name': '',
          'named': false,
          'connector': 'All',
          'not': false,
          'autoAdded': '',
          'filters': []
        }]
      tsBulkQuery['queries'][0]['query']['filters_obj']['filterGroups'][0]['filters'].append({
        'filterField': 'dst_as',
        'operator': '=',
        'filterValue':  ','.join(cGroup)
      })
      tsBulkQuery['queries'][0]['query']['starting_time'] = tsSlice['start']
      tsBulkQuery['queries'][0]['query']['ending_time'] = tsSlice['end']
    
      # Make Query
      print ('Quering Kentik for Timeseries Data Group: ' + str(workingGroup) + ' Time Slice ' + str(tsSlice['start']))
      print('For ' + str(len(cGroup)) + ' customers')
      print('Submited Queries ' + str(len(tsBulkQuery['queries'])))
      
      endTime = datetime.datetime.now() + datetime.timedelta(seconds=10)
      
      customerTSData = kAPI.topXQuery(tsBulkQuery)
      
      # Space request to not overun the API
      while True:
        if datetime.datetime.now() >= endTime:
          break
    
      print('Recived ' + str(len(customerTSData['results'])) + ' responses')
    
      # Loop through results, combine and normlize
      groupCount = 1
      for result in customerTSData['results']:
        print('Recived ' + str(len(result['data'])) + ' responses in response ' + str(groupCount))
        groupCount = groupCount + 1
        for key in result['data']:
          objTSKey = list(key['timeSeries'].keys()) # Get the field becuse it can be any demision
          tsData = []
          for datapoint in key['timeSeries'][objTSKey[0]]['flow']:
            tsData.append({
              'timeIndex': datapoint[0],
              'value': datapoint[1]
            })
          fondKey = next((x for x in combinedTSData if x['name'] == key['key']), None)
          if fondKey:
            # print ('Fond ' + key['key'] + ' Results Count: ' + str(len(result['data'])))
            fondKey['timeSeries'].append(tsData.copy())
          else:
            # print ('Adding ' + key['key'] + ' Results Count: ' + str(len(result['data'])))
            combinedTSData.append({
              'name': key['key'],
              'metric': objTSKey[0],
              'timeSeries': tsData.copy()
            })
          key = None
        result = None
      customerTSData = None
      print ()
    
  return combinedTSData

kAPI = setupKentikAPI()

print ('Setting up arguments')
arguments = args()

print ('Getting Time Slices for Data Query')
slices = getTimeSlices(arguments.queryStartTime, arguments.queryEndTime, arguments.queryResultion)
print ()

print ('Getting Customers from Kentik... (can take several seconds)')
customers = getCustomers(arguments.queryStartTime, arguments.queryEndTime)
print ('Groupping Customers')
customerGroups = groupCustomers(customers)
print (str(len(customers)) + ' customers in ' + str(len(customerGroups)) + ' groups')
secToComplete = len(customerGroups) * len(slices) * 10
TimeToComplete = datetime.datetime.now() + datetime.timedelta(seconds=secToComplete)
print ('Expedcted to complete in ' + str(math.floor(secToComplete/60)) + ' munites at ' + str(TimeToComplete))
print ()
tsData = getTSData(customerGroups, slices)

print ('Making Baselines')
base = baseline.Baselines()
firstBase = base.build_roll_up(3600, 95, tsData) # Find p95 per hour
# Example: For the p95% for the same hour of the same day of the week using hourly roll ups as the input "build_baseline(168, 95. rollup)"
# nth [int]: The nth element to be in each array = Logicly this also means the number of arrays :) too
# pTarget [int]: The pN% target; 95 = p95%
baseline = base.build_baseline(168, 95, firstBase)

print ('Checking for events')
# base.get_alerts(alertWindowSize, alertSameWindow, eventsPerAlert, eventWindowSize, baselineStartIndex, baselineWindow, aboveBase, metricType, baselines, ts)
# 2 events within 10mins and every event with in 10mins is an alert where an event is a any mesurement with in 1min over 100% of the baseline using tsData as the input ts data
alerts = base.get_alerts(600, 600, 2, 60, 0, 3600, 100, 'precent', baseline, tsData)

# Filter to only report clients with attacks
print ('Just Atacks')
print ()
atacks = []
for atack in alerts:
  if len(atack['alerts']) > 0:
    atacks.append(atack.copy())
baseline = None
tsData = None
alerts = None
print (str(len(atacks)) + ' Atacks Fond: ')
print (atacks)
print ()

print ('Writing to csv')
if not os.path.exists('./output'):
    os.makedirs('./output')
with open('./output/kentik_historic_events.csv', 'w') as csv_file:
  csv_file.write('CustomerASN, StartTime, EndTime, Length, Value, Metric\n')
  for customer in atacks:
    for atack in customer:
      csv_file.write(customer['name'] + ',' + atack['start'] + ',' +  atack['end'] + ',' +  atack['length'] + ',' +  atack['value'] + ',' +  customer['metric'] + '\n')
  csv_file.close()
atacks = None
print ('Alerts wrtien too ./output/kentik_historic_events.csv')

# TODO: Output to Graph (seaborn https://seaborn.pydata.org/examples/different_scatter_variables.html)
print ('Making Graph')
atackDS = pd.read_csv('./output/kentik_historic_events.csv')
sns.set(style='whitegrid')
sns.set_context('poster')
f, ax = plt.subplots(figsize=(6.5, 6.5))
sns.despine(f, left=True, bottom=True)
kah = sns.scatterplot(x='StartTime', y='Value',
                hue='CustomerASN', size='Length',
                palette='Blues_d',
                sizes=(1, 8), linewidth=0,
                data=diamonds, ax=ax)
print ('Saving Graph Image to ./output/kentik_historic_events.png')
plt.savefig('./output/kentik_historic_events.png')
print ('Showing Graph Image')
plt.show()