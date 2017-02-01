#####The followings explain the order of running scripts and processing data in order to conduct route choice validation for fast-trips:

---
## 1. Translate observed data into inputs to run FT

### 1.1. [OBS\_to\_DynoDemand](OBS_to_DynoDemand)

**1.1.1.**
Run [*add\_SFtaz\_to\_OBS.py*](OBS_to_DynoDemand/MTCmaz_to_SFtaz/add_SFtaz_to_OBS.py) to convert MTC orig/dest maz's in original OBS file (*OBSdata\_wBART.csv*) to SF taz's and creates *OBSdata\_wBART\_wSFtaz.csv*.

**1.1.2.** Run [*OBS\_to\_DynoDemand.py*](OBS_to_DynoDemand/OBS_to_DynoDemand.py) to convert *OBSdata\_wBART\_wSFtaz.csv* to Dyno-Demand inputs (*household.txt*, *person.txt* and *trip_list.txt*) for running FT.


### 1.2. CHTS\_to\_DynoDemand
TBA ...



---
## 2. Translate observed data into FT output format for Tableau comparison

### 2.1. [OBS\_to\_FToutput](OBS_to_FToutput)
**2.1.1.** Run [*add\_StopID\_OBS.py*](OBS_to_FToutput/Add_StopID_OBS/add_StopID_OBS.py) to find corresponding stop_id's for boarding/alighting locations in OBS file (*OBSdata\_wBART\_wSFtaz.csv*) by matching stops' lat/long, and produces *OBSdata\_wBART\_wSFtaz\_wStops.csv*.

**2.1.2.** Run [OBS\_to\_FToutput.py](OBS_to_FToutput/OBS_to_FToutput.py) to convert *OBSdata\_wBART\_wSFtaz\_wStops.csv* to FT passenger links output format (*OBS\_FToutput.csv*).


### 2.2. [CHTS\_to\_FToutput](CHTS_to_FToutput)

**2.2.1.** Run [*CHTS\_to\_FToutput.py*](CHTS_to_FToutput/CHTS_to_FToutput.py) to convert CHTS gps trips data (*w_gpstrips.csv*) to FT passenger links output format (*CHTS_FToutput.csv*).

**2.2.2.** Run [*add\_StopID\_RouteID\_CHTS.py*](CHTS_to_FToutput/add_StopID_RouteID_CHTS.py) to find corresponding stop_id for A node/B node in *CHTS\_FToutput.csv* by matching lat/long and operator\_type, and produces *CHTS_FToutput_wStops_wRoutes.csv*.



---
## 3. Prepare Tableau comparison visualization dashboard

### 3.1. 
TBA ...

### 3.2. 
TBA ...