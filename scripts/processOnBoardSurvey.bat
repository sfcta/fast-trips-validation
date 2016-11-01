::
:: Runs all On Board Survey scripts to create dyno-demand and dyno-path formatted versions
::
:: This can be run in any directory as long as the environment variables below are set

:: These are Lisa's settings
if %USERNAME%==lzorn (
  rem set OBS_RAW_FILE=M:\Data\OnBoard\Data and Reports\_data Standardized\share_data\survey.csv
  set OBS_RAW_FILE=C:\Users\lzorn\Box Sync\SHRP C-10\3-Transit Demand\OBS_fasttrips_demand\OBSdata_wBART.csv
  set MTCMAZ_TO_SFTAZ_FILE=C:\Users\lzorn\Box Sync\SHRP C-10\4-Transit Rider Behavior\mtcmaz_to_sftaz.csv
  set OBS_GTFS_ROUTE_FILE=C:\Users\lzorn\Box Sync\SHRP C-10\4-Transit Rider Behavior\OBS_GTFS_route_dict.xlsx
  set NETWORK_DIR=C:\Users\lzorn\Box Sync\SHRP C-10\2-Network Supply\sfcta\network_draft1.9
  set CODE_DIR=C:\Users\lzorn\Documents\fast-trips-validation
  set FT_CODE_DIR=C:\Users\lzorn\Documents\fast-trips-develop
)

:: copy the raw On Board Survey data file into place
copy "%OBS_RAW_FILE%" OBSdata_wBART.csv
:: copy the MTC MAZ to SFCTA TAZ mapping into place
copy "%MTCMAZ_TO_SFTAZ_FILE%" .
:: copy the OBS to GTFS route dictionary into place
copy "%OBS_GTFS_ROUTE_FILE%" .


:: ===================== fasttrips input (Dyno-Demand) ==================================================================

:: Add the SFTAZ version of the origin and destination
::   Reads: OBSdata_wBART.csv, mtcmaz_to_sftaz.csv
::  Writes: OBSdata_wBART_wSFtaz.csv
python "%CODE_DIR%\scripts\OBS_to_DynoDemand\MTCmaz_to_SFtaz\add_SFtaz_to_OBS.py"
if errorlevel 1 goto error

:: Convert the on board survey data into the fasttrips input format (Dyno-Demand)
::   Reads: OBSdata_wBART_wSFtaz.csv, DepartureTimeCDFs.dat
::  Writes: household.txt, person.txt, trip_list.txt
python "%CODE_DIR%\scripts\OBS_to_DynoDemand\OBS_to_DynoDemand.py"
if errorlevel 1 goto error

:: ===================== fasttrips ouptput (Dyno-Path) ==================================================================
:: Add the stop ID
::  Reads: OBSdata_wBART_wSFtaz.csv, stops.txt
:: Writes: OBSdata_wBART_wSFtaz_wStops.csv
set PYTHONPATH=%FT_CODE_DIR%
python "%CODE_DIR%\scripts\OBS_to_FToutput\Add_StopID_OBS\add_StopID_OBS.py" "%NETWORK_DIR%"
if errorlevel 1 goto error

:: Create the dyno-path version of the On Board Survey
::  Reads: trip_list.txt, OBSdata_wBART_wSFtaz_wStops.csv
:: Writes: OBS_FToutput_links.csv, OBS_FToutput_paths.csv
python "%CODE_DIR%\scripts\OBS_to_FToutput\OBS_to_FToutput.py"
if errorlevel 1 goto error

:: ===================== map the fasttrips output ==================================================================
:map
copy OBS_FToutput_links.csv pathset_links.csv
copy OBS_FToutput_paths.csv pathset_paths.csv
python "%FT_CODE_DIR%\scripts\create_tableau_path_map.py" "%NETWORK_DIR%" .
if errorlevel 1 goto error

:error