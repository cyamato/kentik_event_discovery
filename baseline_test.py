#!/usr/bin/python3
import baseline
import json

rollup = 300

with open('test.json') as json_file:
    jsData = json.load(json_file)
    
base = baseline.Baselines()
norm = base.normlizeKentik(jsData)
firstBase = base.build_roll_up(rollup, 95, norm)
seondBase = base.build_roll_up(3600, 95, firstBase)
# print (firstBase)
# print (seondBase)
baseline = base.build_baseline(5, 95, firstBase)
# print (baseline)

# base.get_alerts(alertWindowSize, alertSameWindow, eventsPerAlert, eventWindowSize, baselineStartIndex, baselineWindow, aboveBase, metricType, baselines, ts)
# 2 events within 10mins and every event with in 10mins is an alert where an event is a any mesurement with in 1min over 1000 units of the baseline using norm as the input ts data
# alerts = base.get_alerts(600, 600, 2, 60, 0, rollup, 1000, 'unit', baseline, norm)
# print (alerts)

alerts = base.get_alerts(600, 600, 2, 60, 0, rollup, 0, 'unit', baseline, norm)
print (alerts)