#!/usr/bin/python3
# -*- coding: utf-8 -*-
import math
import datetime

class Baselines:
  """
  Class to build and use a baseline from a set of metrics
  """
  def normlizeKentik(self, kentikTSData):
    """
    This function will convert a Kentik Timeserires returned from an API call 
    to a standard format for use in this module
    kentikTSData [obj]:  A Kentik API Query Return Object
    """
    objs = []
    for queries in kentikTSData['results']:
      for obj in queries['data']:
        objTSKey = list(obj['timeSeries'].keys()) # Get the field becuse it can be any demision
        # Format Timeseries
        tsData = []
        for tsObj in obj['timeSeries'][objTSKey[0]]['flow']:
          tsData.append({
            'timeIndex': tsObj[0],
            'value': tsObj[1]
          })
        objs.append({
          'name': obj['key'],
          'metric': objTSKey[0],
          'timeSeries': tsData
        })
    
    tsObj = None
    
    return objs


  def build_roll_up(self, windowSize, pTarget, ts):
    """
    Find the pN% target per window in the time seriers
    windowSize [int]:  The number of seconds to find the pN% in
    pTarget [int]: The pN% target; 95 = p95%
    ts [array]: An array of timeseries data
    """
    baselineObjs = [] # Place to hold baselines
    windowSize = windowSize * 1000 # Adjust windowSize to ns
    
    # Loop through each ts object
    for obj in ts:
      if obj['timeSeries']:
        # Figure out the first window 
        sliceTime = obj['timeSeries'][0]['timeIndex'] # Get the first Timestamp
        sliceTime = math.floor(sliceTime / windowSize) # Get the rounded down number of windows
        sliceTime = sliceTime * windowSize # Get this back in seconds
        maxTimeInSlice = sliceTime + windowSize # Get the end of the slice time window
        
        # Loop to extract the target per window
        window = [] # Am empty array to hold the time series data for the window
        rollUps = [] # An empty array to hold pN%s
        for timeSlice in obj['timeSeries']:
          if timeSlice['timeIndex'] < maxTimeInSlice: # We are with in the curent window
            window.append(timeSlice['value'])  # Add timeslices metric value
            nothingInThisTimeSlice = False
          else: # Not in the window
            if window:  # We have stuff in the buffer to add
              l = len(window) # Get the number of elements in the slice
              i = math.floor(l * (pTarget / 100)) # Find the pN% element index
              
              # Sort the array
              window = sorted(window)
              
              rollUps.append({
                'timeIndex': sliceTime,
                'value': window[i]
              })
            else:
              rollUps.append({
                'timeIndex': sliceTime,
                'value': None
              })
            sliceTime = maxTimeInSlice # Rest to next window
            maxTimeInSlice = maxTimeInSlice + windowSize
            window = [] # Empty Window
            window.append(timeSlice['value']) # Add new slice
        
        # Process the last one if there is any
        if window:
          l = len(window) # Get the number of elements in the slice
          i = math.floor(l * (pTarget / 100)) # Find the pN% element index
          
          # Sort array
          window = sorted(window)
          
          rollUps.append({
            'timeIndex': sliceTime,
            'value': window[i]
          })
          
        # Add computing rollup for TS Object into baselineObjs
        baselineObjs.append({
          'name': obj['name'],
          'metric': obj['metric'],
          'timeSeries': rollUps
        })
        
    # We clean up after our selves
    windowSize = None
    pTarget = None
    ts = None
    window = None
    rollUps = None
    l = None
    i = None
    
    return baselineObjs
          
  def build_baseline(self, nth, pTarget, ts):
    """
    This function will find the pN% element in a artray of every nth ts mesurment
    For exsample build an arrays of every 3rd element and find p50% element
    input = [1,2,3,4,5,6,7,8,9,10,11,12,13,14]
    output =
    [
      [1,4,7,10,13] = 7
      [2,5,8,11,14] = 8
      [3,6,9,12] = 6
    ]
    nth [int]: The nth element to be in each array = Logicly this also means the number of arrays :) too
    pTarget [int]: The pN% target; 95 = p95%
    ts [array]: An array of timeseries data
    """
    # Loop through each target
    baselines = [] # An epmty array for adding baseline objects for each object
    for obj in ts:
      groups = [[]] * nth # An empty array to hold our nth groups
      nthCount = 0
      # Add each nth element in the nth array
      for tsValue in obj['timeSeries']:
        groups[nthCount].append(tsValue)
        nthCount = nthCount + 1
        if nthCount == nth:
          nthCount = 0
      
      #find the nth element
      baseline = [] # An empty array to hold our baseline objects
      for group in groups:
        l = len(group)
        i = math.floor(l * (pTarget / 100)) # Find the pN% element index
        
        # Sort our list
        group = sorted(group, key = lambda i: i['value'])
        t = datetime.datetime.fromtimestamp(group[i]['timeIndex']/1000)
        year, week, weekday = t.isocalendar()
        baseline.append({
          'year': t.year,
          'month': t.month,
          'week': week,
          'day': t.day,
          'dayOfWeek': weekday, # Monday = 1; Sunday = 7
          'hour': t.hour,
          'minute': t.minute,
          'second': t.second,
          'time': t,
          'value': group[i]['value']
        })
      
      # Add full baseline for this object to our otput array baselines
      baselines.append({
        'name': obj['name'],
        'baseline': baseline
      })
      
    return baselines
  