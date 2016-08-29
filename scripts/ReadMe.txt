#####The followings explains the order of running scripts and processing data in order to conduct route choice validation for fast-trips:

---
## 1. Translate observed data into inputs to run FT

### 1.1. [OBS\_to\_DynoDemand](https://github.com/psrc/fast-trips-validation/tree/master/scripts/OBS_to_DynoDemand)

**1.1.1.**
Run [*add\_SFtaz\_to\_OBS.py*](https://github.com/psrc/fast-trips-validation/blob/master/scripts/OBS_to_DynoDemand/MTCmaz_to_SFtaz/add_SFtaz_to_OBS.py) to convert MTC orig/dest maz's in original OBS file (*OBSdata\_wBART.csv*) to SF taz's and creates *OBSdata\_wBART\_wSFtaz.csv*.

**1.1.2.** Run [*OBS\_to\_DynoDemand.py*](https://github.com/psrc/fast-trips-validation/blob/master/scripts/OBS_to_DynoDemand/OBS_to_DynoDemand.py) to convert *OBSdata\_wBART\_wSFtaz.csv* to Dyno-Demand inputs (*household.txt*, *person.txt* and *trip_list.txt*) for running FT.

---
### 1.2. CHTS\_to\_DynoDemand
TBA ...



---
## 2. Translate observed data into FT output format for Tableau comparison

### 2.1. [OBS\_to\_FToutput](https://github.com/psrc/fast-trips-validation/tree/master/scripts/OBS_to_FToutput)
**2.1.1.** Run [*add\_StopID\_OBS.py*](https://github.com/psrc/FastTrips_PathChoice_Validation/blob/master/OBS_to_FToutput/Add_StopID_OBS/add_StopID_OBS.py) to find corresponding stop_id's for boarding/alighting locations in OBS file (*OBSdata\_wBART\_wSFtaz.csv*) by matching stops' lat/long, and produces *OBSdata\_wBART\_wSFtaz\_wStops.csv*.

**2.1.2.** Run [OBS\_to\_FToutput.py](https://github.com/psrc/FastTrips_PathChoice_Validation/blob/master/OBS_to_FToutput/OBS_to_FToutput.py) to convert *OBSdata\_wBART\_wSFtaz\_wStops.csv* to FT passenger links output format (*OBS\_FToutput.csv*).


---
### 2.2. [CHTS\_to\_FToutput](https://github.com/psrc/FastTrips_PathChoice_Validation/tree/master/CHTS_to_FToutput)

Run [*CHTS\_to\_FToutput.py*](https://github.com/psrc/FastTrips_PathChoice_Validation/blob/master/CHTS_to_FToutput/CHTS_to_FToutput.py) to convert CHTS gps trips data (*w_gpstrips.csv*) to FT passenger links output format (*CHTS_FToutput.csv*).



---
## 3. Prepare Tableau comparison visualization dashboard

### 3.1. 
TBA ...

### 3.2. 
TBA ...