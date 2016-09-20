#####Finds corresponding stop_id's for all boarding/alighting locations in OBS file by matching stops' lat/long, service_id's and route_id's.

---
##### Reads: 
OBSdata_wBART_wSFtaz.csv, OBS_GTFS_route_dict.xlsx

##### Writes:
OBSdata_wBART_wSFtaz_wStops.csv

---
#### Prerequisites:
* This script uses Fast-Trips library, so in order to run it, Fast-Trips should be installed (See instructions [here](https://github.com/MetropolitanTransportationCommission/fast-trips/tree/develop#setup)).