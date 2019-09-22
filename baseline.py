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
    Example: For the p95% for the same hour of every day using hourly roll ups as the input "build_baseline(24, 95. rollup)"
    Example: For the p95% for the same hour of the same day of the week using hourly roll ups as the input "build_baseline(168, 95. rollup)"
    nth [int]: The nth element to be in each array = Logicly this also means the number of arrays :) too
    pTarget [int]: The pN% target; 95 = p95%
    ts [array]: An array of timeseries data
    
    Retrurns [array]: of baselines - Note: an dict with the element 'value' is used and not an int so that extra tags such as Day or hour can be added by the user
    """
    # Loop through each target
    baselines = [] # An epmty array for adding baseline objects for each object
    for obj in ts:
      groups = []
      for i in range(0, nth):
        groups.append(obj['timeSeries'][i::nth])
          
      #find the nth element
      baseline = [] # An empty array to hold our baseline objects
      for group in groups:
        l = len(group)
        i = math.floor(l * (pTarget / 100)) # Find the pN% element index

        # Sort our list
        group = sorted(group, key = lambda i: i['value'])
        baseline.append({
          'value': group[i]['value']
        })
      
      # Add full baseline for this object to our otput array baselines
      baselines.append({
        'name': obj['name'],
        'baseline': baseline
      })
      
    return baselines
    
  def getTargetFromBaseLine(self, baselineValue, aboveBase, metricType):
    """
    baselineValue [int]: baseline value from which to set trigger
    aboveBase [int]: Trigger level above baseline (Can be negative)
    metricType [string{unit,precent}]: aboveBase type
    """
    if metricType == 'unit':
      triggerPoint = baselineValue + aboveBase
    else:
      triggerPoint = baselineValue * (1+(aboveBase/100))
    
    return triggerPoint
  
  def checkForEvent(self, aboveBase, datapoint, triggerPoint, events, alertWindowSize, alerts, alertSameWindow, eventsPerAlert):
    if ((aboveBase > -1 and datapoint['value'] > triggerPoint) or (aboveBase < 0 and datapoint['value'] < triggerPoint)):
      events = self.addEvent(events, alertWindowSize, datapoint)
      alerts = self.checkForAlert(alerts, alertSameWindow, eventsPerAlert, events, datapoint)
    
    return events, alerts
  
  def addEvent(self, events, alertWindowSize, datapoint):
    """
    This function adds events, element time out, and count returns newEventList
    events [array]: An array of timestamps
    datapoint [obj]: A TS object
    """
    ageout = datapoint['timeIndex'] - alertWindowSize
    newEventList = [] # A new empty event
    
    # Do TTL upkeep
    for event in events:
      if event > ageout:
        newEventList.append(event)
        
    # Add Event
    newEventList.append(datapoint['timeIndex'])
    return newEventList
    
  def checkForAlert(self, alerts, alertSameWindow, eventsPerAlert, events, event):
    """
    This function will check for alerts
    alerts [array]: An array of alerts
    alertSameWindow [int]: The number of seconds in which new events are part of the same alert
    eventsPerAlert [int]: The number of events in the alertWindow to activate an alert
    events [array]: An array of timestamps
    event [obj]: A timeseriers datapoint
    """
    if len(events) >= eventsPerAlert:
      if (alerts and (alerts[-1]['timeIndex'] + alertSameWindow) > event['timeIndex']):
        # Same alert
        if alerts[-1]['value'] < event['value']:
          # Set alert to peak metric
          alerts[-1]['value'] = event['value']
        alerts[-1]['end'] = event['timeIndex']
      else:
        # New alert
        alerts.append({
          'start': event['timeIndex'],
          'end': event['timeIndex'],
          'value': event['value']
        })
    return alerts
  
  def get_alerts(self, alertWindowSize, alertSameWindow, eventsPerAlert, eventWindowSize, baselineStartIndex, baselineWindow, aboveBase, metricType, baselines, ts):
    """
    This function looks for events in Kentik query normlized timeseries data based on a set of baslines
    alertWindowSize [int]: The number of seconds for the size of window in which to look for an alert
    alertSameWindow [int]: The number of seconds in which new events are part of the same alert
    eventsPerAlert [int]: The number of events in the alertWindow to activate an alert
    eventWindowSize [int]: The number of seconds for the size of window in which to look for an event
    baselineStartIndex [int]: The first baseline to match to
    baselineWindow [int]: The number of seconds each base line incroment represnts
    aboveBase [int]: Trigger level above baseline (Can be negative)
    metricType [string{unit,precent}]: aboveBase type
    baselines [array]: An array of baseline objects from the build_baseline function of this class
    ts [array]: An array of Kentik Query normlized timeseries data object from the normlizeKentik function of this class
    """
    alertWindowSize = alertWindowSize * 1000
    alertSameWindow = alertSameWindow * 1000
    eventWindowSize = eventWindowSize * 1000
    baselineWindow = baselineWindow * 1000
    allAlerts = [] # An empty array used to hold alerts found for each key
    
    # Loop through each time searies object
    for obj in ts:
      eventFond = False # Var used to indecate an event was found in this window
      alertObj = {
        'name': obj['name'],
        'metric': obj['metric'],
        'alerts': []
      }
      # Find the right baseline to apply
      baseline = next((item for item in baselines if item['name'] == obj['name']), False)
      if baseline:
        # Set Max time in this baseline value
        timeSlice = int(obj['timeSeries'][0]['timeIndex'])
        timeSlice = math.floor(timeSlice / baselineWindow)
        timeSlice = timeSlice * baselineWindow
        maxTime = timeSlice + baselineWindow
        triggerPoint = self.getTargetFromBaseLine(baseline['baseline'][baselineStartIndex]['value'], aboveBase, metricType)
        events = [] # An array to hold found events
        alerts = [] # An array to hold alerts
        
        # Loop through each ts datapoint
        for datapoint in obj['timeSeries']:
          # Check if we need to change up baseline to next window
          if datapoint['timeIndex'] < maxTime:
            events, alerts = self.checkForEvent(aboveBase, datapoint, triggerPoint, events, alertWindowSize, alerts, alertSameWindow, eventsPerAlert)
          else:
            maxTime = maxTime + baselineWindow
            baselineStartIndex = baselineStartIndex + 1
            if baselineStartIndex >= len(baseline['baseline']):
              baselineStartIndex = 0
            triggerPoint = self.getTargetFromBaseLine(baseline['baseline'][baselineStartIndex]['value'], aboveBase, metricType)
            events, alerts = self.checkForEvent(aboveBase, datapoint, triggerPoint, events, alertWindowSize, alerts, alertSameWindow, eventsPerAlert)
        
        alertObj['alerts'] = alerts
        
        # Clean
        timeSlice = None
        maxTime = None
        triggerPoint = None
        events = None
        alerts = None
        
      allAlerts.append(alertObj)
    
    return allAlerts