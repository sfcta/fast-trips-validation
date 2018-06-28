# fast-trips-validation

This repository contains scripts to transform both the transit On-Board Survey (OBS) and California Household Travel Survey (CHTS) to both [dyno-demand][demand-standard-url] and [dyno-path][dyno-path-url] formats. In addition, there are also scripts to process both survey data and Fast-Trips output data (in [dyno-path][dyno-path-url] format) and summarize them for calibration and validation purposes. These scripts create input files that can be plugged into Tableau Dashboards. All the scripts can be found in the [scripts](scripts/) directory of this repository.

- [CHTS to DynoDemand Conversion](#chts-to-dynodemand-conversion)
- [CHTS to DynoPath Conversion](#chts-to-dynopath-conversion)
- [Validation DashBoard](#validation-dashboard)
- [OBS to DynoDemand Conversion](#obs-to-dynodemand-conversion)
- [OBS to DynoPath Conversion](#obs-to-dynopath-conversion)

## CHTS to DynoDemand Conversion
The scripts(s) for converting CHTS gps data into deno-demand format currently reside in a separate repository. Please click [here][ft-demand-url] for more details.

## CHTS to DynoPath Conversion
This section describes the conversion of CHTS gps data into dyno-path format. The primary input file is based on GPS traces and is called `w_gpstrips.csv`. Due to privacy restrictions, this file is available and needs to be processed only on SFCTA servers. However, the following scripts could be adapted to process any survey data with adequate details about transit trips and convert to [dyno-path][dyno-path-url] format. Some of these scripts use Fast-Trips library, so in order to run them, Fast-Trips should be installed (see instructions [here][ft-setup-url])

1. [CHTS_to_FToutput.py](scripts/CHTS_to_DynoPath/CHTS_to_FToutput.py): this script takes in `w_gpstrips.csv` file from CHTS as input and identifies distinct transit trips and various components such as sub-mode, access/egress, transfer etc. There are some assumptions regarding maximum walk time, initial wait time, transfer wait time etc. The output file is called `CHTS_ft_output.csv`.

    * max access/egress walk = 50 min
    * max initial wait time = 30 min
    * max transfer wait time = 20 min
    * max time to get off the transit vehicle = 2 min

2. [add_StopID_RouteID_CHTS_v2.py](scripts/CHTS_to_DynoPath/add_StopID_RouteID_CHTS_v2.py): the latest version of this script uses `CHTS_ft_output.csv` as input and based on lat-long and time stamp information, attempts to identify not only transit stops (boarding/alighting/transfer) but also specific transit trips (service ids) for a given transit network and schedule ([GTFS-Plus][gtfs-plus-url]). This helps in the identification of the detailed transit path that could have been used by the respondent which in turn can be compared to that found by Fast-Trips. The output file is `CHTS_FToutput_wStops_wRoutes_v2.csv`.

3. **Add Origin/Destination TAZ**: the processed output file from the previous step contains the origin and destination lat-longs of transit trips. These need to be geocoded to TAZs so that TAZ-TAZ level transit demand can be generated and then run through Fast-Trips path-finding. The paths found by Fast-Trips can be validated against those inferred from survey GPS traces. Geocoding needs to be done using an offline process (for example using ArcGIS) in which `A_lon,A_lat` are mapped to `A_TAZ` (origin zone) and `B_lon,B_lat` are mapped to `B_TAZ` (destination zone). The output file is `CHTS_FToutput_wTAZ.csv` which will have two more columns (`A_TAZ` and `B_TAZ`) in addition to the columns in `CHTS_FToutput_wStops_wRoutes_v2.csv`.

4. [output_dynopath.py](scripts/CHTS_to_DynoPath/output_dynopath.py): this is the final step that outputs the converted survey in dyno-path format. However, it needs to be run in two steps: 
- In the first step (`RUNMODE = 1`), the script computes a few additional variables and outputs the `pathset_links.csv` file. This file is used by the dyno-demand conversion script to generate a demand file for Fast-Trips as a trip list (see [here][ft-demand-url] for more details about developing demand files).
- The trip file in turn is used as an additional input in the second step (`RUNMODE = 2`) to output `pathset_paths.csv` file.

## Validation Dashboard
This section describes using Fast-Trips output and survey data (both in [dyno-path][dyno-path-url] format) to create input files for a calibration and validation dashboard in Tableau. The calibration and validation process would first involve running the demand/trip list from observed data (CHTS or OBS in this case) through Fast-Trips and then comparing the modeled and observed transit paths. The various metrics used for the comparison are prepared using the following script.

[DynoPath_to_Tableau.py](scripts/CHTS_Validation/DynoPath_to_Tableau.py): this needs the locations of observed CHTS transit paths in dyno-path format (prepartion described in [CHTS to DynoPath Conversion](#chts-to-dynopath-conversion) section above) and the model output paths among other network inputs. The script generates two output files, `pathset_compare.csv` and `pathset_compare_melt.csv`, which are in turn used by Tableau validation dashboard. 

Once output files are generated using the script above, the Validation Dashboard template workbook `Validation_DashBoard.twb` needs to be downloaded (from [here](tableau/)) and the two data sources need to be replaced ([Tableau Data Source Replacement][tableau-replace-url]) to update the metrics in the dashboard.

## OBS to DynoDemand Conversion

1. [add_SFtaz_to_OBS.py](scripts/OBS_to_DynoDemand/MTCmaz_to_SFtaz/add_SFtaz_to_OBS.py): Converts MTC origin/destination MAZs in original OBS file (OBSdata_wBART.csv) to SF TAZs and adds them as two new columns to OBS file, producing OBSdata_wBART_wSFtaz.csv.

2. [OBS_to_DynoDemand.py](scripts/OBS_to_DynoDemand/OBS_to_DynoDemand.py): converts OBSdata_wBART_wSFtaz.csv to [Dyno-Demand] [demand-standard-url] files (trip_list.txt, household.txt, person.txt).

### Assumptions:

1. Value of time was calculated using the following rules: (based on [SFCTA RPM-9 Report](https://drive.google.com/file/d/0B0tvdqs1FsGZcTBhRms3aXJqZGs/view?pli=1), p39):
    * Non-work VoT = 2/3 work VoT,
    * Impose a minimum of $1/hour and a maximum of $50/hour,
    * Impose a maximum of $5/hour for workers younger than 18 years old.

2. OBS only contains departure hour (and not minutes). In order to translate these hours into hour-minutes, departure hour distributions (`DepartureTimeCDFs.dat`) have been generated based on time period distributions in `PreferredDepartureTime.dat`.

## OBS to DynoPath Conversion

1. [add_StopID_OBS.py](scripts/OBS_to_DynoPath/Add_StopID_OBS/add_StopID_OBS.py): Finds corresponding stop_id's for all boarding/alighting locations in OBS by matching stops' lat/long, service_id and route_id with those in GTFS PLus network data, producing OBSdata_wBART_wSFtaz_wStops.csv.

2. [OBS_to_DynoPath.py](scripts/OBS_to_DynoPath/OBS_to_DynoPath.py): converts OBSdata_wBART_wSFtaz_wStops.csv to [Dyno-Path] [dyno-path-url].

Notes: 
* This conversion is being done for the purpose of validation, and the output file does not necessarily contain all the required attributes designed for dyno-path format.
* [add_StopID_OBS.py](scripts/OBS_to_DynoPath/Add_StopID_OBS/add_StopID_OBS.py) uses Fast-Trips library, so in order to run it, Fast-Trips should be installed (See instructions [here][ft-setup-url]).

[demand-standard-url]: <https://github.com/osplanning-data-standards/dyno-demand>
[dyno-path-url]: <https://github.com/osplanning-data-standards/dyno-path>
[gtfs-plus-url]: <https://github.com/osplanning-data-standards/GTFS-PLUS>
[ft-setup-url]: <https://github.com/BayAreaMetro/fast-trips/tree/develop#setup>
[ft-demand-url]: <https://github.com/sfcta/fast-trips_demand_converter>
[tableau-replace-url]: <https://onlinehelp.tableau.com/current/pro/desktop/en-us/connect_basic_replace.html>
