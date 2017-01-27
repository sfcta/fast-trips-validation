##### Converts On-Board Survey (OBS) data to dyno-path format:

* **[add\_StopID\_OBS.py](Add_StopID_OBS/add_StopID_OBS.py)** finds corresponding stop_id's for all boarding/alighting locations in OBS by matching stops' lat/long, service_id and route_id with those in GTFS PLus network data, producing OBSdata\_wBART\_wSFtaz\_wStops.csv
* **[OBS\_to\_FToutput.py](OBS_to_FToutput.py)** converts OBSdata\_wBART\_wSFtaz\_wStops.csv to *[dyno-path format](https://github.com/osplanning-data-standards/dyno-path)*.

---
#### Notes:
This conversion is being done for the purpose of validation, and the output file does not necessarily contain all the required attributes designed for dyno-path format. 

---
#### Prerequisites:
* [add\_StopID\_OBS.py](Add_StopID_OBS/add_StopID_OBS.py) uses Fast-Trips library, so in order to run it, Fast-Trips should be installed (See instructions [here](https://github.com/MetropolitanTransportationCommission/fast-trips/tree/develop#setup)).