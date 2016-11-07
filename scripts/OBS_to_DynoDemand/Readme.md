##### Converts On-Board Survey (OBS) data to DynoDemand files:

* **[add\_SFtaz\_to_OBS.py](MTCmaz_to_SFtaz/add_SFtaz_to_OBS.py)** converts MTC origin/destination maz's in OBS to SF taz's and adds them as two new columns to OBS file, producing OBSdata\_wBART\_wSFtaz.csv
* **[OBS\_to\_DynoDemand.py](OBS_to_DynoDemand.py)** converts OBSdata\_wBART\_wSFtaz.csv to *[Dyno-Demand] (https://github.com/osplanning-data-standards/dyno-demand)* files (trip\_list.txt, household.txt, person.txt).

---
### Assumptions:

1. Value of time was calculated using the following rules: (based on [SFCTA RPM-9 Report](https://drive.google.com/file/d/0B0tvdqs1FsGZcTBhRms3aXJqZGs/view?pli=1), p39):

 * Non-work VoT = 2/3 work VoT,
 * Impose a minimum of $1/hour and a maximum of $50/hour,
 * Impose a maximum of $5/hour for workers younger than 18 years old.

2. OBS only contains departure hour (and not minutes). In order to translate these hours into hour-minutes, departure hour distributions [(DepartureTimeCDFs.dat)](DepartureTimeCDFs.dat) have been generated based on time period distributions in [PreferredDepartureTime.dat](PreferredDepartureTime.dat).
