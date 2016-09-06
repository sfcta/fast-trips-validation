######################################################################################################
# Finds corresponding stop_id's for boarding/alighting locations in OBS file by matching stops' lat/long
# Reads: OBSdata_wBART_wSFtaz.csv, GTFS Plus network
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
    original_columns = [
        'operator',
        'Unique_ID',
        'ID',
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
        'onoff_exit_station']
    # Keep only the columns we're interested
    df = df[original_columns]
    # Add the service_id to match the network data
    df["service_id"] = df["operator"].replace(OBS_OPERATOR_TO_NETWORK_SERVICE)
    # This will print a few lines into the log so the columns are clear
    fasttrips.FastTripsLogger.info("observed person trips=\n%s" % str(df.head()))
    # These are the operators
    fasttrips.FastTripsLogger.info("operator value_counts()=\n%s" % str(df["operator"].value_counts()))

    # ===========================================================
    # process one operator at a time, for memory reasons and debugging

    new_df = pd.DataFrame()
    df_operators_series = df["operator"].value_counts()
    for operator in df_operators_series.keys():

        fasttrips.FastTripsLogger.info("======================== %s ========================" % operator)

        # select the possible vehicle trips for this service
        service_vehicle_trips = full_trips_df.loc[ full_trips_df["service_id"] == OBS_OPERATOR_TO_NETWORK_SERVICE[operator] ]
        # select the observed person trips for this service
        service_person_trips  = df.loc[df["operator"] == operator]

        fasttrips.FastTripsLogger.info("service_vehicle_trips=\n%s" % str(service_vehicle_trips.head()))
        fasttrips.FastTripsLogger.info("service_person_trips=\n%s" % str(service_person_trips.head()))

        # For now, process just those operators for whom we join on service only and not route
        #
        # TODO:
        # for other operators, we probably want to join using Elizabeth's route bridge, so join on both service_id and route_id
        # so that the stops are specific to the service + route
        if operator != "BART" and operator != "Caltrain": continue

        # first collect unique stops for the operator
        service_unique_vehicle_stops = service_vehicle_trips[["service_id","stop_id","stop_name","stop_lat","stop_lon"]].drop_duplicates()
        fasttrips.FastTripsLogger.info("service_unique_vehicle_stops (%d)=\n%s" % (len(service_unique_vehicle_stops), str(service_unique_vehicle_stops)))

        # add columns: survey_board_stop_id  survey_board_stop_name  survey_board_stop_lat  survey_board_stop_lon  survey_board_stop_dist
        service_person_trips = get_closest_stop(service_person_trips, service_unique_vehicle_stops, "survey_board")

        # add columns: survey_alight_stop_id survey_alight_stop_name  survey_alight_stop_lat  survey_alight_stop_lon  survey_alight_stop_dist
        service_person_trips = get_closest_stop(service_person_trips, service_unique_vehicle_stops, "survey_alight")

        fasttrips.FastTripsLogger.info("service_person_trips = \n%s" % str(service_person_trips.head()))

        # TODO: guess stop IDs for first_board and last_alight, looking at the first_board_tech and last_alight_tech?

        # put this operator's rows into the new dataframe
        if len(new_df) == 0:
            new_df = service_person_trips
        else:
            new_df = new_df.append(service_person_trips, ignore_index=True)

    # this is really to assert column order
    all_columns = original_columns
    all_columns.extend(["survey_board_stop_id",  "survey_board_stop_name", "survey_board_stop_lat", "survey_board_stop_lon", "survey_board_stop_dist",
                        "survey_alight_stop_id", "survey_alight_stop_name","survey_alight_stop_lat","survey_alight_stop_lon","survey_alight_stop_dist"])

    new_df = new_df[all_columns]

    new_df.to_csv("OBSdata_wBART_wSFtaz_wStops.csv", index=False)