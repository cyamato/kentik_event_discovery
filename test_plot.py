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

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

import kentik
import baseline

if os.path.isfile('./output/buffer_cache.json'):
  with open('./output/buffer_cache.json.json') as buffer_cache:
    tsData = json.load(buffer_cache)
    buffer_cache.close()

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