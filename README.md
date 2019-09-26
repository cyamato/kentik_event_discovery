# Kentik Event Discovery
[![GitHub release](https://img.shields.io/github/v/release/cyamato/kentik_event_discovery)](https://github.com/cyamato/kentik_event_discovery/releases)
[![GitHub license](https://img.shields.io/github/license/cyamato/kentik_event_discovery)](https://github.com/cyamato/kentik_event_discovery/blob/master/LICENSE)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)

A simple tool to analyze historical data from the Kentik Data Engine for past 
events.  This tool will query Kentik for customers and then recursively collect 
data at a defined resolution and time period for all customers.  Generating a 
baseline and applying a policy to the customer data from Kentik this tool will 
extract events as CSV and Graph Image files.

## Installation

There are two options for installing and running this tool

* As a Docker Container(s) - Preferred
* As a local Python Script

#### Docker Container:
```bash
cd ~
git clone https://github.com/cyamato/kentik_event_discovery.git
cd ./kentik_event_discovery
nano ./docker-compose.yml
```
Edit the ./docker-compose.yml file to set the "khistory" service's Kentik API
environment variables

```yaml
    environment:
      - KENTIK_API_USER="johndoe@expans.com"
      - KENTIK_API_PASSWORD="adsf8960svypzsyadf06g"
```
#### Local Python Script:
```bash
cd ~
python3 -m pip install --user --upgrade pip
python3 -m pip install --user virtualenv
git clone https://github.com/cyamato/kentik_event_discovery.git
cd ./kentik_event_discovery
python3 -m venv kentik_event_discovery
source kentik_event_discovery/bin/activate
pip3 install -r requirements.txt 
export KENTIK_API_USER="johndoe@expans.com"
export KENTIK_API_PASSWORD="adsf8960svypzsyadf06g"
export HARPERDB_URL="harperdb:9925"
export HARPERDB_USER="HDB_ADMIN"
export HARPERDB_PASSWORD="1400"
```

Besure to change the environment variables to your own settings

## Running the tool
#### Docker:
```bash
docker-compose up -d
```
#### Local Python Script:
```bash
./sl.py
```
**Note**:  There is a help screen available by using the command switch "--help"

This tool will cache its progress and pick up where it left off when using a 
local database for caching.

The default baseline formed for each customer is based on the p95% measurement 
per hour by day of the week from 1-minute   bits per second measurements. The 
same hour of the same day of the week policy(eg. 08:00 on Mondays).  This can be 
adjusted in the code (*sl.py:432* and *sl.py:436*) and the 
*"kentik_query_tsData.json"* file.  Please note that *"base.build_roll_up()"*" 
function can be called recursively to create any needed rollups of rollups.  The 
*"base.build_baseline()*" function should only be called once.

The default polcy looks for 2 events 200% above the baseline within 10 minutes 
for each customer.  This can be adjusted in the code (*sl.py:441*) as well.

The JSON queries used for the API calls to the Kentik Data Engine are located in 
the *"./input"* directory.

* **kentik_query_tsData.json**: The JSON query used to collect time-series data 
for each customer
* **kentik_query_customers.json**:  The JSON query used to discover customers


## Output
Several files will be created in the “./output” directory:
* **customer.json**:  A JSON array of customer
* **customer_raw.json**:  A JSON array of the customer with the full name when 
ASNs are used
* **kentik_historic_events.csv**:  A comma value separated file of all events 
found
* **kentik_historic_events.png**:  A graph image plot of all events found in the
data
* **kentik_historic_events_long.png**:  A graph image plot of all events found 
in the data over 1 minute in length

Other files that might be of intrest are:
* **buffer_log.json**: The buffer cache file used to track hashes of the queries
already ran
* **buffer_cache.json**:  The buffer cache file of results if a database is not 
being used

## Contributing
Pull requests are welcome. For major changes, please open an issue first to 
discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
