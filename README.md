# fast-trips-validation

This repository contains scripts to transform both the transit On-Board Survey (OBS) and California Household Travel Survey (CHTS) to both [dyno-demand][demand-standard-url] and [dyno-path][dyno-path-url] formats. In addition, there are also scripts to process both survey data and Fast-Trips output data (in [dyno-path][dyno-path-url] format) and summarize them for calibration and validation purposes. These scripts create input files that can be plugged into Tableau Dashboards. All the scripts can be found in the [scripts](scripts/) directory of this repository.

- [CHTS to DynoPath Conversion](#chts-to-dynopath-conversion)
- [CHTS Validation DashBoard](#chts-validation-dashboard)
- [Python Notebooks (old)](#python-notebooks-old)

## CHTS to DynoPath Conversion
This section describes the conversion of CHTS gps data into dyno-path format. The primary input file is based on GPS traces and is called `w_gpstrips.csv`. Due to privacy restrictions, this file is available and needs to be processed only on SFCTA servers. However, the following scripts could be adapted to process any survey data with adequate details about transit trips and convert to [dyno-path][dyno-path-url] format. Some of these scripts use Fast-Trips library, so in order to run them, Fast-Trips should be installed (see instructions [here][ft-setup-url])

1. [CHTS_to_FToutput.py](scripts/CHTS_to_DynoPath/CHTS_to_FToutput.py): this script takes in `w_gpstrips.csv` file from CHTS as input and identifies distinct transit trips and various components such as sub-mode, access/egress, transfer etc. There are some assumptions regarding maximum walk time, initial wait time, transfer wait time etc. The output file is called `CHTS_ft_output.csv`.

2. [add_StopID_RouteID_CHTS_v2.py](scripts/CHTS_to_DynoPath/add_StopID_RouteID_CHTS_v2.py): the latest version of this script uses `CHTS_ft_output.csv` as input and based on lat-long and time stamp information, attempts to identify not only transit stops (boarding/alighting/transfer) but also specific transit trips (service ids) for a given transit network and schedule ([GTFS-Plus][gtfs-plus-url]). This helps in the identification of the detailed transit path that could have been used by the respondent which in turn can be compared to that found by Fast-Trips. The output file is `CHTS_FToutput_wStops_wRoutes_v2.csv`.

3. **Add Origin/Destination TAZ**: the processed output file from the previous step contains the origin and destination lat-longs of transit trips. These need to be geocoded to TAZs so that TAZ-TAZ level transit demand can be generated and then run through Fast-Trips path-finding. The paths found by Fast-Trips can be validated against those inferred from survey GPS traces. Geocoding needs to be done using an offline process (for example using ArcGIS) in which `A_lon,A_lat` are mapped to `A_TAZ` (origin zone) and `B_lon,B_lat` are mapped to `B_TAZ` (destination zone). The output file is `CHTS_FToutput_wTAZ.csv`.

4. [output_dynopath.py](scripts/CHTS_to_DynoPath/output_dynopath.py): this is the final step that outputs the converted survey in dyno-path format. However, it needs to be run in two steps: 
- In the first step (`RUNMODE = 1`), the script computes a few additional variables and outputs the `pathset_links.csv` file. This file is used by the dyno-demand conversion script to generate a demand file for Fast-Trips as a trip list (see [here][ft-demand-url] for more details about developing demand files).
- The trip file in turn is used as an additional input in the second step (`RUNMODE = 2`) to output `pathset_paths.csv` file.

## CHTS Validation Dashboard
This section describes using Fast-Trips output and survey data (both in [dyno-path][dyno-path-url] format) to create input files for a calibration and validation dashboard in Tableau. The calibration and validation process would first involve running the demand/trip list from observed data (CHTS in this case) through Fast-Trips and then comparing the modeled and observed transit paths. The various metrics used for the comparison are prepared using the following script.

[DynoPath_to_Tableau.py](scripts/CHTS_Validation/DynoPath_to_Tableau.py): this needs the locations of observed CHTS transit paths in dyno-path format (prepartion described in [CHTS to DynoPath Conversion](#chts-to-dynopath-conversion) section above) and the model output paths among other network inputs. The script generates two output files, `pathset_compare.csv` and `pathset_compare_melt.csv`, which are in turn used by Tableau validation dashboard. 

Once output files are generated using the script above, the Validation Dashboard template workbook `Validation_DashBoard.twb` needs to be downloaded (from [here](tableau/)) and the two data sources need to be replaced ([Tableau Data Source Replacement][tableau-replace-url]) to update the metrics in the dashboard.

## Python Notebooks (old)

### Generate Tableau Input

Tableau workbooks depend on 2 output files generated by **notebooks/prepare_fasttrips.ipynb**. The notebook reads a set of fast-trips standard outputs and a list of observed trips for comparison. Set the directory for these inputs ("OUTPUT_DIR" and "obs_links_dir") in the upper cells. (Note that observed records are not available on GitHub due to privacy restrictions.)

Outputs generated from the script include:
- path_comparison.csv
- chosenpath_links_with_observed.csv

Other configurations in the top cell include:
- "threshold"
    - only include paths above a given probability threshold 
- "comparison field"
    - when comparing trips, specify whether matches are based on modes, agencies, or routes

### Update Tableau

Download dashboard: https://public.tableau.com/profile/brice.nichols#!/vizhome/OBS-ValidationDRAFT/FastTripsOverview-OBS
Open with Tableau Public/Desktop.

Navigate to Data Source tab, and select "Edit Connection" under Connections pane. Point to the latest output from the notebooks. 
Update the location for "chosenpaths_links" and "path_comparison" data sources. "Path_intersection" is an additional output from the notebook that may be required to be updated as well, but is no longer used in the dashboard. 

[demand-standard-url]: <https://github.com/osplanning-data-standards/dyno-demand>
[dyno-path-url]: <https://github.com/osplanning-data-standards/dyno-path>
[gtfs-plus-url]: <https://github.com/osplanning-data-standards/GTFS-PLUS>
[ft-setup-url]: <https://github.com/BayAreaMetro/fast-trips/tree/develop#setup>
[ft-demand-url]: <https://github.com/sfcta/fast-trips_demand_converter>
[tableau-replace-url]: <https://onlinehelp.tableau.com/current/pro/desktop/en-us/connect_basic_replace.html>
