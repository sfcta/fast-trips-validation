#####Converts On-Board Survey Demand (OBS) to [Dyno-Demand] (https://github.com/osplanning-data-standards/dyno-demand).

---
##### Reads: 
OBS.csv, [DepartureTimeCDFs.dat](https://github.com/psrc/OBS-to-DynoDemand-Converter/blob/master/DepartureTimeCDFs.dat) 

##### Writes:
[household.txt](https://github.com/osplanning-data-standards/dyno-demand/blob/master/files/household.md), [person.txt](https://github.com/osplanning-data-standards/dyno-demand/blob/master/files/person.md), [trip\_list.txt](https://github.com/osplanning-data-standards/dyno-demand/blob/master/files/trip_list.md)

---
### Assumptions:

1. For 'work_status’ data, OBS has only two categories: ‘non-worker’ or ‘full- or part-time’; while in person.txt full-time and part-time are two different categories. Since full-time is more often, all the ‘full/part time’ values were translated to 'full-time'.
2. Value of time was calculated using the following rules: (based on [SFCTA RPM-9 Report](https://drive.google.com/file/d/0B0tvdqs1FsGZcTBhRms3aXJqZGs/view?pli=1), p39):

 * Non-work VoT = 2/3 work VoT,
 * Impose a minimum of $1/hour and a maximum of $50/hour,
 * Impose a maximum of $5/hour for workers younger than 18 years old.

3. OBS only contains departure hour (and not minutes). In order to translate these hours into hour-minutes, departure hour distributions [(DepartureTimeCDFs.dat)](https://github.com/psrc/OBS-to-DynoDemand-Converter/blob/master/DepartureTimeCDFs.dat) have been generated in based on time period distributions in [PreferredDepartureTime.dat](https://github.com/sfcta/fast-trips_demand_converter/blob/master/PreferredDepartureTime.dat).

---
### Prerequisites:
* OBS.csv should have no comma within field values. However, commas exist in the original file in the fields of household\_income (e.g. 75,000), fare\_medium 
(e.g. exempt (employee, law enforcement)) and also language (e.g. Chinese, Mandarin). To solve this, simply replace ",000" by "000" and also ", " by "/" before running the script.

* MTC orig/dest maz's in OBS file should have first be converted to SF taz's, by running [add\_SFtaz\_to_OBS.py](https://github.com/psrc/FastTrips_PathChoice_Validation/blob/master/OBS_to_DynoDemand/MTCmaz_to_SFtaz/add_SFtaz_to_OBS.py) .