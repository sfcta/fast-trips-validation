######################################################################################################
# Finds corresponding stop_id's for boarding/alighting locations in OBS file by matching stops' lat/long
# Reads: OBSdata_wBART_wSFtaz.csv, GTFS Plus network, OBS_GTFS_route_dict.xlsx
# Writes: OBSdata_wBART_wSFtaz_wStops.csv
#######################################################################################################
import pandas as pd
import fasttrips
import argparse, sys

# bridge from on board survey operator => network service_id
OBS_OPERATOR_TO_NETWORK_SERVICE = {
    "BART"                          :"bart_weekday",
    "AC Transit"                    :"ac_transit_weekday",
    "Caltrain"                      :"caltrain_weekday",
    "SamTrans"                      :"samtrans_weekday",
    "SF Muni Pilot"                 :"sf_muni_weekday",
    "Tri-Delta"                     :"tri_delta_transit_weekday",
    "Golden Gate Transit (bus)"     :"golden_gate_transit_weekday",
    "County Connection"             :"cccta_weekday",
    "Santa Rosa CityBus"            :"santa_rosa_weekday",
    "Golden Gate Transit (ferry)"   :"golden_gate_transit_weekday", # or should this be ferry_weekday?
    "ACE"                           :"ace_weekday",
    "Napa Vine"                     :"vine_weekday",
    "LAVTA"                         :"lavta_weekday",
    "SF Bay Ferry"                  :"ferry_weekday",
    "Sonoma County"                 :"sonoma_county_transit_weekday",
    "Union City"                    :"union_city_transit_weekday",
    "Petaluma"                      :"petaluma_weekday"
}

# Creating route dictionary from OBS to GTFS-1.8 route
route_bridge = pd.read_excel('OBS_GTFS_route_dict.xlsx','Sheet1')
route_bridge.index = route_bridge.OBS_route
route_bridge = route_bridge.drop('OBS_route',axis=1)
OBS_ROUTE_TO_GTFS_ROUTE = route_bridge.to_dict()['GTFS1.8_route']

def get_closest_stop(person_trips_df, vehicle_stops_df, person_prefix):
    """
    Given a datafram containint person trips and dataframe containing a set of stops, performs an inner join on the two dataframes
    so that each stop is checked against each person trip.

    Then calculates the distances between those stops and the lat/lon specified by [person_prefix]_(lat|lon), and chooses
    the closest stop.

    Returns person_trips_df but with the additional columns:
    * [person_prefix]_stop_id
    * [person_prefix]_stop_lat
    * [person_prefix]_stop_lon
    * [person_prefix]_stop_name
    * [person_prefix]_stop_dist
    """
    # join the person trips with the stops
    person_trips_by_stops_df = pd.merge(left=person_trips_df,
                                        right=vehicle_stops_df,
                                        how="inner")

    # calculate the distance from [person_prefix]_lat, [person_prefix]_lon, and the stop
    fasttrips.Util.calculate_distance_miles(person_trips_by_stops_df,
                                            origin_lat="%s_lat" % person_prefix, origin_lon="%s_lon" % person_prefix,
                                            destination_lat="stop_lat",          destination_lon="stop_lon",
                                            distance_colname="%s_stop_dist" % person_prefix)
    # fasttrips.FastTripsLogger.info("person_trips_by_stops_df=\n%s" % person_trips_by_stops_df.head(50))

    # get the closest stop
    person_trips_df = person_trips_by_stops_df.loc[ person_trips_by_stops_df.groupby("Unique_ID")["%s_stop_dist" % person_prefix].idxmin() ]

    # rename the new columns
    person_trips_df.rename(columns={"stop_id"  :"%s_stop_id"   % person_prefix,
                                    "stop_name":"%s_stop_name" % person_prefix,
                                    "stop_lat" :"%s_stop_lat"  % person_prefix,
                                    "stop_lon" :"%s_stop_lon"  % person_prefix}, inplace=True)

    # fasttrips.FastTripsLogger.info("person_trips_df=\n%s" % person_trips_df.head(50))
    return person_trips_df

if __name__ == "__main__":

    pd.set_option('display.width',      1000)
    pd.set_option('display.max_rows',   1000)
    pd.set_option('display.max_columns', 100)

    parser = argparse.ArgumentParser()
    parser.add_argument("network_dir", type=str, help="Location of GTFS-Plus network")
    args = parser.parse_args(sys.argv[1:])

    # Initialize fasttrips; we'll use it to read the network
    fasttrips.FastTripsLogger.info("Reading network from [%s]" % args.network_dir)
    ft = fasttrips.FastTrips(input_network_dir= args.network_dir,
                             input_demand_dir = None,
                             output_dir       = ".")

    # Read the input network files
    ft.read_input_files()
    # Get the full (joined) transit vehicle trip table
    full_trips_df = ft.trips.get_full_trips()
    # We also want longitude and latitude for the stops
    full_trips_df = ft.stops.add_stop_lat_lon(full_trips_df, id_colname="stop_id", new_lat_colname="stop_lat", new_lon_colname="stop_lon", new_stop_name_colname="stop_name")
    # This will print a few lines into the log so the columns are clear
    fasttrips.FastTripsLogger.info("full_trips_df=\n%s" % str(full_trips_df.head()))
    # These are the service_ids
    fasttrips.FastTripsLogger.info("service_id value_counts()=\n%s" % str(full_trips_df["service_id"].value_counts()))

    # Read the observed person trips file
    df = pd.read_csv('OBSdata_wBART_wSFtaz.csv')
    # Keep only the columns we're interested
    df = df[[
        'operator',
        'Unique_ID',
        'access_mode',
        'egress_mode',
        'route',
        'boardings',
        'survey_tech',
        'first_board_tech',
        'last_alight_tech',
        'transfer_from',
        'transfer_to',
        'first_board_lat',
        'first_board_lon',
        'survey_board_lat',
        'survey_board_lon',
        'survey_alight_lat',
        'survey_alight_lon',
        'last_alight_lat',
        'last_alight_lon',
        'orig_maz',
        'orig_sf_taz',
        'dest_maz',
        'dest_sf_taz',
        'day_part',
        'onoff_enter_station',
        'onoff_exit_station'
        ]]
    # Add the service_id to match the network data
    df["service_id"] = df["operator"].replace(OBS_OPERATOR_TO_NETWORK_SERVICE)
    # Add the route_id to match the network data
    df["route"] = df["operator"] + '_' + df["route"] #route dict reads data in the [operator]_[route] format
    df["route_id"] = df["route"].replace(OBS_ROUTE_TO_GTFS_ROUTE)
    df["route_id"].fillna("none", inplace=True)

    # This will print a few lines into the log so the columns are clear
    fasttrips.FastTripsLogger.info("observed person trips=\n%s" % str(df.head()))
    # These are the operators
    fasttrips.FastTripsLogger.info("operator value_counts()=\n%s" % str(df["operator"].value_counts()))

    # ===========================================================
    # process one operator at a time, for memory reasons and debugging
    
    Locations = ['first_board','survey_board','survey_alight','last_alight']
    survey_board_stops = pd.DataFrame()
    survey_alight_stops = pd.DataFrame()
    first_board_stops = pd.DataFrame()
    last_alight_stops = pd.DataFrame()

    df_operators_series = df["operator"].value_counts()
    for operator in df_operators_series.keys():

        fasttrips.FastTripsLogger.info("======================== %s ========================" % operator)

        # select the possible vehicle trips for this service
        service_vehicle_trips = full_trips_df.loc[ full_trips_df["service_id"] == OBS_OPERATOR_TO_NETWORK_SERVICE[operator] ]
        # select the observed person trips for this service
        service_person_trips  = df.loc[df["operator"] == operator]

        fasttrips.FastTripsLogger.info("service_vehicle_trips=\n%s" % str(service_vehicle_trips.head()))
        fasttrips.FastTripsLogger.info("service_person_trips=\n%s" % str(service_person_trips.head()))

        # For BART and Caltrain, and also those where route_id is missing, we join on service_id only and not route_id,
        # for other operators, we join on both service_id and route_id, so that the stops are specific to the service + route.
        if operator == "BART" or operator == "Caltrain":

            # first collect unique stops for the operator
            service_unique_vehicle_stops = service_vehicle_trips[["service_id","stop_id","stop_name","stop_lat","stop_lon"]].drop_duplicates()
            for i in Locations:
                # add columns: [location]_stop_id  [location]_stop_name  [location]_stop_lat  [location]_stop_lon
                stops = get_closest_stop(service_person_trips, service_unique_vehicle_stops, i)
                stops = stops[['Unique_ID', i+'_stop_id', i+'_stop_name', i+'_stop_lat', i+'_stop_lon']]
                # creates individual [location] dataframes to be joined with df later.
                # this prevents removing records where stops' lat/lon exist for one [Location] and not for the other.
                if   i=='survey_board'  : survey_board_stops  = survey_board_stops.append(stops, ignore_index=True)
                elif i=='survey_alight' : survey_alight_stops = survey_alight_stops.append(stops, ignore_index=True)
                elif i=='first_board'   : first_board_stops   = first_board_stops.append(stops, ignore_index=True)
                else                    : last_alight_stops   = last_alight_stops.append(stops, ignore_index=True)

        else:
            service_unique_vehicle_stops = service_vehicle_trips[["route_id","service_id","stop_id","stop_name","stop_lat","stop_lon"]].drop_duplicates()
            for i in Locations:
                stops = get_closest_stop(service_person_trips, service_unique_vehicle_stops, i)
                stops = stops[['Unique_ID', i+'_stop_id', i+'_stop_name', i+'_stop_lat', i+'_stop_lon']]
                if   i=='survey_board'  : survey_board_stops  = survey_board_stops.append(stops, ignore_index=True)
                elif i=='survey_alight' : survey_alight_stops = survey_alight_stops.append(stops, ignore_index=True)
                elif i=='first_board'   : first_board_stops   = first_board_stops.append(stops, ignore_index=True)
                else                    : last_alight_stops   = last_alight_stops.append(stops, ignore_index=True)
    
            # those not BART or Caltrain, but w/ missing route_id
            service_unique_vehicle_stops = service_vehicle_trips[["service_id","stop_id","stop_name","stop_lat","stop_lon"]].drop_duplicates()
            service_person_trips = service_person_trips.loc[service_person_trips['route_id']=='none']
            for i in Locations:
                stops = get_closest_stop(service_person_trips, service_unique_vehicle_stops, i)
                stops = stops[['Unique_ID', i+'_stop_id', i+'_stop_name', i+'_stop_lat', i+'_stop_lon']]
                if   i=='survey_board'  : survey_board_stops  = survey_board_stops.append(stops, ignore_index=True)
                elif i=='survey_alight' : survey_alight_stops = survey_alight_stops.append(stops, ignore_index=True)
                elif i=='first_board'   : first_board_stops   = first_board_stops.append(stops, ignore_index=True)
                else                    : last_alight_stops   = last_alight_stops.append(stops, ignore_index=True)
        
        # TODO: guess stop IDs for first_board and last_alight, looking at the first_board_tech and last_alight_tech?

    # Put all stop_id info into the dataframe
    new_df = df
    new_df = pd.merge (new_df, survey_board_stops,  how='left', on='Unique_ID')
    new_df = pd.merge (new_df, survey_alight_stops, how='left', on='Unique_ID')
    new_df = pd.merge (new_df, first_board_stops,   how='left', on='Unique_ID')
    new_df = pd.merge (new_df, last_alight_stops,   how='left', on='Unique_ID')
 
    new_df.to_csv("OBSdata_wBART_wSFtaz_wStops.csv", index=False)