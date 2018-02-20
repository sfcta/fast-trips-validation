###################################################################################
# For each transit leg in CHTS_FToutput.csv this script attempts to identify the 
# specific transit trip_id from a given network based on the closest stops to 
# boarding/alighting locations and closest transit service to boarding/alighting times.
# Reads: CHTS_FToutput.csv
# Writes: CHTS_FToutput_wStops_wRoutes.csv
####################################################################################
import pandas as pd
import multiprocessing, sys, os, traceback, datetime
import fasttrips

NETWORK_DIR = r"Q:\Model Development\SHRP2-fasttrips\Task2\built_fasttrips_network_2012Base\draft1.14_fare"
TRIPS_INPUT_FILE = "CHTS_ft_output.csv"
OUTPUT_FILE = "CHTS_FToutput_wStops_wRoutes_v2.csv"
NUMBER_OF_PROCESSES = 6

# bridge from CHTS travel_mode => operator_type
CHTS_MODE_TO_OPERATOR_TYPE = {
    15 : "Local_bus/Rapid_bus",
    16 : "GoldenGate/AC_transit",
    #19 : None,
    20 : "AirBART",
    23 : "Local_bus/Rapid_bus",
    24 : "BART",
    25 : "ACE/Caltrain",
    26 : "MuniMetro/VTA",
    27 : "Street_car/Cable_car",
    29 : "Ferry"
}

OP_TO_NETAGENCY = {
    15: ['sf_muni','ac_transit','samtrans','santa_rosa','lavta','scvta','sonoma_county_transit','union_city_transit',
         'petaluma','tri_delta_transit','cccta','vine','soltrans'],
    16: ['ac_transit','golden_gate_transit'],
    20: ['airbart'],
    23: ['sf_muni','ac_transit','samtrans','santa_rosa','lavta','scvta','sonoma_county_transit','union_city_transit',
         'petaluma','tri_delta_transit','cccta','vine','soltrans'],
    24: ['bart'],
    25: ['caltrain','ace'],
    26: ['sf_muni','scvta'],
    27: ['sf_muni'],
    29: ['ferry']
}

# bridge from network service_id => operator_type
NETWORK_AGENCY_TO_OPERATOR_TYPE = {
    "bart"                  :"BART",
    "airbart"               :"AirBART",
    "ac_transit"            :"GoldenGate/AC_transit",
    "caltrain"              :"ACE/Caltrain",
    "samtrans"              :"Local_bus/Rapid_bus",
    "golden_gate_transit"   :"GoldenGate/AC_transit",
    "santa_rosa"            :"Local_bus/Rapid_bus",
    "ace"                   :"ACE/Caltrain",
    "lavta"                 :"Local_bus/Rapid_bus",
    "scvta"                 :"Local_bus/Rapid_bus",
    "sonoma_county_transit" :"Local_bus/Rapid_bus",
    "union_city_transit"    :"Local_bus/Rapid_bus",
    "petaluma"              :"Local_bus/Rapid_bus",
    "tri_delta_transit"     :"Local_bus/Rapid_bus",
    "cccta"                 :"Local_bus/Rapid_bus",
    "vine"                  :"Local_bus/Rapid_bus",
    "soltrans"              :"Local_bus/Rapid_bus",
    "ferry"                 :"Ferry",
    "sf_muni"               :"sf_muni"
}



muni_operations = ["Local_bus/Rapid_bus", "MuniMetro/VTA", "Street_car/Cable_car"]
MAX_STOP_DIST = 0.3 # max distance for stop_id matching based on stops' lat/lon
MAX_TIME_DIFF = pd.Timedelta(minutes=30)

def get_closest_stop(trip_rec, vehicle_stops_df, location_prefix):
    
    col_names = list(trip_rec.columns)
    df = vehicle_stops_df.merge(trip_rec, on='op_type', how='left')
    # calculate the distance from [location_prefix]_lat, [location_prefix]_lon, and the stop
    fasttrips.Util.calculate_distance_miles(df,
                                            origin_lat="%s_lat" % location_prefix, origin_lon="%s_lon" % location_prefix,
                                            destination_lat="stop_lat",            destination_lon="stop_lon",
                                            distance_colname="stop_dist")
    # get the stops that are within a user defined range
    df = df.loc[(df['stop_dist'] < MAX_STOP_DIST) & (pd.notnull(df['stop_dist'])),]
    if location_prefix=='A':
        time_var = 'board_time'
        time_var2 = 'departure_time'
    else:
        time_var = 'alight_time'
        time_var2 = 'arrival_time'

    beg_time = (pd.to_datetime(trip_rec[time_var].iloc[0]) - MAX_TIME_DIFF).time()
    end_time = (pd.to_datetime(trip_rec[time_var].iloc[0]) + MAX_TIME_DIFF).time()
    df['temp_time'] = pd.to_datetime(df[time_var2]).dt.time
    df = df.loc[(df['temp_time']>=beg_time) & (df['temp_time']<=end_time),]
    df['diff_time'] = (pd.to_datetime(df[time_var2]) - pd.to_datetime(trip_rec[time_var].iloc[0])).dt.total_seconds()
    df['diff_time'] = df['diff_time'].abs()
    df = df.sort_values(['route_id','direction_id','trip_id','stop_dist','diff_time'])
    df = df.drop_duplicates(['route_id','direction_id','trip_id','stop_id'])
#     df = df.loc[df.groupby(['route_id','direction_id'])['stop_dist'].idxmin(),] 
#     df = df.groupby(['route_id','direction_id']).apply(lambda dfg: dfg.nsmallest(3,'stop_dist')).reset_index(drop=True)
    # select top 3 stops for each route and direction based on closest distance and time
    df = df.groupby(['route_id','direction_id']).head(3).reset_index(drop=True)
    # identify a maximum of 30 trip-stop candidate matches
    df = df.head(30)
    df = df.rename(columns={"stop_id"         :"%s_stop_id"   % location_prefix,
                            "stop_name"       :"%s_stop_name"   % location_prefix, 
                            "stop_sequence"   :"%s_seq"   % location_prefix,
                            "stop_dist"       :"%s_stop_dist" % location_prefix,
                            "trip_id"         :"%s_trip_id" % location_prefix,
                            "route_id"        :"%s_route_id" % location_prefix,
                            "service_id"      :"%s_service_id" % location_prefix,
                            "agency_id"       :"%s_agency_id" % location_prefix,
                            })
    new_cols = [(location_prefix+'_'+x) for x in ['stop_id','stop_name','seq','stop_dist','trip_id','route_id','service_id','agency_id']]
    col_names = col_names + new_cols
    return df[col_names]

def find_stop_route(worker_num, todo_queue, done_queue, trips_df):
    """
    Process worker function.  Processes all the records in queue.

    """
    worker_str = "_worker%02d" % worker_num

    from fasttrips.FastTrips import FastTrips
    from fasttrips.Logger      import FastTripsLogger, setupLogging
    setupLogging(infoLogFilename  = None,
                 debugLogFilename = os.path.join(".", FastTrips.DEBUG_LOG % worker_str), 
                 logToConsole     = False,
                 append           = False)
    FastTripsLogger.info("Worker %2d starting" % worker_num)

    while True:
        # go through my queue -- check if we're done
        rec = todo_queue.get()
        if str(rec) == 'DONE':
            break
        # do the work
        try:
            transit_mode_no = rec['transit_mode_no'].iloc[0]
            if rec['linkmode'].iloc[0] == 'transit' and transit_mode_no in CHTS_MODE_TO_OPERATOR_TYPE.keys():
                rec['op_type'] = CHTS_MODE_TO_OPERATOR_TYPE[transit_mode_no]
                req_cols = ['arrival_time','departure_time','stop_id','stop_sequence','trip_id','route_id','direction_id','service_id',
                            'agency_id','stop_lat','stop_lon','stop_name']
                trips_df_sub = trips_df.loc[trips_df['agency_id'].isin(OP_TO_NETAGENCY[transit_mode_no]), req_cols]
                trips_df_sub['op_type'] = CHTS_MODE_TO_OPERATOR_TYPE[transit_mode_no]
                # identify potential trip-stop matches for boarding location
                df_A = get_closest_stop(rec, trips_df_sub, 'A')
#                 FastTripsLogger.debug(df_A)
                # identify potential trip-stop matches for alighting location
                df_B = get_closest_stop(rec, trips_df_sub, 'B')
#                 FastTripsLogger.debug(df_B)
                trips_df_sub = df_A.merge(df_B)
                trips_df_sub = trips_df_sub.loc[trips_df_sub['A_trip_id']==trips_df_sub['B_trip_id'],]
                trips_df_sub = trips_df_sub.loc[trips_df_sub['A_seq'] < trips_df_sub['B_seq'],]
                trips_df_sub['stop_seq_diff'] = trips_df_sub['B_seq'] - trips_df_sub['A_seq']
                trips_df_sub['sum_dist'] = trips_df_sub['A_stop_dist'] + trips_df_sub['B_stop_dist']
                trips_df_sub = trips_df_sub.sort_values(['sum_dist','stop_seq_diff'])
                trips_df_sub = trips_df_sub.head(1)
                if len(trips_df_sub) > 0:
                    rec['A_stop_id'] = trips_df_sub['A_stop_id'].iloc[0]
                    rec['B_stop_id'] = trips_df_sub['B_stop_id'].iloc[0]
                    rec['A_stop_name'] = trips_df_sub['A_stop_name'].iloc[0]
                    rec['B_stop_name'] = trips_df_sub['B_stop_name'].iloc[0]
                    rec['A_seq'] = trips_df_sub['A_seq'].iloc[0]
                    rec['B_seq'] = trips_df_sub['B_seq'].iloc[0]
                    rec['trip_id'] = trips_df_sub['A_trip_id'].iloc[0]
                    rec['route_id'] = trips_df_sub['A_route_id'].iloc[0]
                    rec['service_id'] = trips_df_sub['A_service_id'].iloc[0]
                    rec['agency_id'] = trips_df_sub['A_agency_id'].iloc[0]
                else:
                    rec['A_stop_id'] = ''
                    rec['B_stop_id'] = ''
                    rec['A_stop_name'] = ''
                    rec['B_stop_name'] = ''
                    rec['A_seq'] = ''
                    rec['B_seq'] = ''
                    rec['trip_id'] = ''
                    rec['route_id'] = ''
                    rec['service_id'] = ''
                    rec['agency_id'] = ''
            else:
                rec['A_stop_id'] = ''
                rec['B_stop_id'] = ''
                rec['A_stop_name'] = ''
                rec['B_stop_name'] = ''
                rec['A_seq'] = ''
                rec['B_seq'] = ''
                rec['trip_id'] = ''
                rec['route_id'] = ''
                rec['service_id'] = ''
                rec['agency_id'] = ''
            done_queue.put(rec)
        except:
            FastTripsLogger.exception("Exception")
            # call it a day
            done_queue.put( (worker_num, "EXCEPTION", str(sys.exc_info()) ) )
            break

if __name__ == "__main__":
    start_time = datetime.datetime.now()
    
    ## Read FT network input files and get transit trips information
    ft = fasttrips.FastTrips(input_network_dir= NETWORK_DIR,
                             input_demand_dir = None,
                             input_weights    = None,
                             run_config       = None,
                             output_dir       = ".")
    fasttrips.FastTripsLogger.info("Reading network from [%s]" % NETWORK_DIR)
    
    ft.read_input_files()
    # Get the full (joined) transit vehicle trip table and add lat/lon for the stops
    full_trips_df = ft.trips.get_full_trips()
    full_trips_df = ft.stops.add_stop_lat_lon(full_trips_df, id_colname="stop_id", new_lat_colname="stop_lat", new_lon_colname="stop_lon", new_stop_name_colname="stop_name")
#     full_trips_df.to_csv('full_trips.csv', index=False)
#     sys.exit()
#     full_trips_df = pd.read_csv('full_trips.csv')
    
    fasttrips.FastTripsLogger.info("**************************** MATCHING STOPS AND ROUTES **********************************************")
    start_time          = datetime.datetime.now()
    process_dict        = {}  # workernum -> {"process":process, "alive":alive bool, "done":done bool, "working_on":(person_id, trip_list_num)}
    todo_queue          = None
    done_queue          = None
    
    
    try:
        # Setup multiprocessing processes
        if NUMBER_OF_PROCESSES > 1:
            todo_queue      = multiprocessing.Queue()
            done_queue      = multiprocessing.Queue()
            for process_idx in range(1, 1+NUMBER_OF_PROCESSES):
                fasttrips.FastTripsLogger.info("Starting worker process %2d" % process_idx)
                process_dict[process_idx] = {
                    "process":multiprocessing.Process(target=find_stop_route,
                    args=(process_idx, todo_queue, done_queue, full_trips_df)),
                    "alive":True,
                    "done":False
                }
                process_dict[process_idx]["process"].start()
            
            # Read CHTS observed person trips file created in the previous step using CHTS_to_FToutput.py
            df = pd.read_csv(TRIPS_INPUT_FILE)
            orig_cols = list(df.columns)
            # Add Unique_ID to be used for merging later on
            df['Unique_ID'] = df.index
            for i in df.index:
                row = df.loc[[i],]
                todo_queue.put(row)
                     
            result_df = pd.DataFrame()
            for i in df.index:
                result_df = pd.concat([result_df,done_queue.get()])
            # we're done, let each process know
            for process_idx in process_dict.keys():
                todo_queue.put('DONE')
            # join up my processes
            for process_idx in process_dict.keys():
                process_dict[process_idx]["process"].join()
            print '%s join done!' %datetime.datetime.now()
            result_df = result_df.sort_values(['Unique_ID'])
            result_df = result_df[orig_cols+['op_type','A_stop_id','B_stop_id','trip_id','service_id','agency_id','route_id','A_stop_name','B_stop_name','A_seq','B_seq']]
            result_df.to_csv(OUTPUT_FILE, index=False)
            
     
    except (KeyboardInterrupt, SystemExit):
        exc_type, exc_value, exc_tb = sys.exc_info()
        fasttrips.FastTripsLogger.error("Exception caught: %s" % str(exc_type))
        error_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        for e in error_lines: fasttrips.FastTripsLogger.error(e)
        fasttrips.FastTripsLogger.error("Terminating processes")
        # terminating my processes
        for proc in process_dict:
            proc.terminate()
        raise
    except:
        # some other error
        exc_type, exc_value, exc_tb = sys.exc_info()
        error_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        for e in error_lines: fasttrips.FastTripsLogger.error(e)
        raise
    
    time_elapsed = datetime.datetime.now() - start_time
    total_time_str = "All Done. Time elapsed: %2dh:%2dm:%2ds" %(int(time_elapsed.total_seconds() / 3600),
                                                            int((time_elapsed.total_seconds() % 3600) / 60),
                                                            time_elapsed.total_seconds() % 60)
    fasttrips.FastTripsLogger.info(total_time_str)
    print total_time_str