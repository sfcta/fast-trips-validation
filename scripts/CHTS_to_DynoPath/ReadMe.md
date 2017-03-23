##### Converts California Household Travel Survey (CHTS) data to dyno-path format:

* **[CHTS\_to\_FToutput.py](CHTS_to_FToutput.py)** converts CHTS gps trips data (w\_gpstrips.csv) to *[dyno-path format](https://github.com/osplanning-data-standards/dyno-path)*, producing CHTS\_FToutput.csv, and
* **[add\_StopID\_RouteID\_CHTS.py](add_StopID_RouteID_CHTS.py)** finds corresponding stop_id for A node/B node in CHTS\_FToutput.csv by matching lat/long and operator\_type with those in GTFS-PLUS network data, and produces CHTS\_FToutput\_wStops\_wRoutes.csv. Operator\_type represents operation and is defined based on mode\_num.

---
### Assumptions:
CHTS gps trips file (w_gpstrips.csv) contains all the movements a person made during a day, with no obvious indicator for different types of trips. So, some assumptions has been made to identify transit trips out of all the movements:

* max access/egress walk = 50 min 
* max initial wait time = 30 min
* max transfer wait time = 20 min
* max time to get off the transit vehicle = 2 min

---
#### Prerequisites:
* [add\_StopID\_RouteID\_CHTS.py](add_StopID_RouteID_CHTS.py) uses Fast-Trips library, so in order to run it, Fast-Trips should be installed (See instructions [here](https://github.com/MetropolitanTransportationCommission/fast-trips/tree/develop#setup)).