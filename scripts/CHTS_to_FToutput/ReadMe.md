**[CHTS\_to\_FToutput.py](CHTS_to_FToutput.py)** converts CHTS gps trips data to FT [passenger links](https://github.com/lmz/dyno-path/blob/patch-1/files/links.md) output format, and 
**[add\_StopID\_RouteID\_CHTS.py](add_StopID_RouteID_CHTS.py)** finds corresponding stop_id for A node/B node in CHTS_FToutput.csv by matching lat/long and operator_type with those in GTFS-PLUS network data. Operator_type represents operation and is defined based on mode_num.

---
### Assumptions:
CHTS gps trips file (w_gpstrips.csv) contains all the movements a person made during the day, and there is no obvious indicator for different sets of trips. So, some assumptions has been made to identify transit trips out of all the movements being made throughout the day.

* max access/egress walk = 50 min 
* max initial wait time = 30 min
* max transfer wait time = 20 min
* max egress time (to get off the transit vehicle) = 2 min

---
#### Prerequisites:
* This script uses Fast-Trips library, so in order to run it, Fast-Trips should be installed (See instructions [here](https://github.com/MetropolitanTransportationCommission/fast-trips/tree/develop#setup)).