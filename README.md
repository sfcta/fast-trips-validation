# fast-trips-validation

This repository contains scripts to transform both the transit On-Board Survey (OBS) and California Household Travel Survey (CHTS) to both [dyno-demand][demand-standard-url] and [dyno-path][dyno-path-url] formats. In addition, there are also scripts to process both survey data and Fast-Trips output data (in [dyno-path][dyno-path-url] format) and summarize them for calibration and validation purposes. These scripts create input files that can be plugged into Tableau Dashboards. All the scripts can be found in the [scripts](scripts/) directory of this repository.

- [CHTS to DynoPath Conversion](#chts-to-dynopath-conversion)
- [CHTS Validation DashBoard](#chts-validation-dashboard)
- [Python Notebooks (old/deprecated)](#python-notebooks-old)

## CHTS to DynoPath Conversion
This section describes the conversion of CHTS gps data into dyno-path format. The primary input file is based on GPS traces and is called `w_gpstrips.csv`. Due to privacy restrictions, this file is available and needs to be processed only on SFCTA servers. However, the following scripts could be adapted to process any survey data with adequate details about transit trips and convert to [dyno-path][dyno-path-url] format.

1. [CHTS_to_FToutput.py](scripts/CHTS_to_DynoPath/CHTS_to_FToutput.py): this script takes in `w_gpstrips.csv` file from CHTS as input and identifies distinct transit trips and various components such as sub-mode, access/egress, transfer etc. There are some assumptions regarding maximum walk time, initial wait time, transfer wait time etc. The output file is called `CHTS_ft_output.csv`.

2. [add_StopID_RouteID_CHTS_v2.py](scripts/CHTS_to_DynoPath/add_StopID_RouteID_CHTS_v2.py): the latest version of this script uses `CHTS_ft_output.csv` as input and based on lat-long and time stamp information, attempts to identify not only transit stops (boarding/alighting/transfer) but also specific transit trips (service ids) for a given transit network and schedule ([GTFS-Plus][gtfs-plus-url]). This helps in the identification of the detailed transit path that could have been used by the respondent which in turn can be compared to that found by Fast-Trips. The output file is `CHTS_FToutput_wStops_wRoutes_v2.csv`.

## CHTS Validation Dashboard
This section describes using Fast-Trips output and survey data (both in dyno-path format) to create input files for a calibration and validation dashboard in Tableau.

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

