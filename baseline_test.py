#!/usr/bin/python3
import baseline
import json

with open('test.json') as json_file:
    jsData = json.load(json_file)
    
base = baseline.Baselines()
norm = base.normlizeKentik(jsData)
firstBase = base.build_roll_up(60, 95, norm)
seondBase = base.build_roll_up(3600, 95, firstBase)
print (len(firstBase[1]["timeSeries"]))
print (len(seondBase[1]["timeSeries"]))
baseline = base.build_baseline(5, 95, firstBase)
print (len(baseline[0]['baseline']))