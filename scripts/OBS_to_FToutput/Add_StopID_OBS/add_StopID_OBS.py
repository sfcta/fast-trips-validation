######################################################################################################
# Finds corresponding stop_id's for boarding/alighting locations in OBS file by matching stops' lat/long
# Reads: OBSdata_wBART_wSFtaz.csv, GTFS Plus network, OBS_GTFS_route_dict.xlsx
# Writes: OBSdata_wBART_wSFtaz_wStops.csv
#######################################################################################################
import pandas as pd
import numpy
import fasttrips
import argparse, sys

# File containing mapping OBS traits to GTFS-plus network traits
OBS_to_GTFSPLUS = 'OBS_GTFS_route_dict.xlsx'

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
    # join the person trips with the stops -- this will join on common columns
    person_trips_by_stops_df = pd.merge(left=person_trips_df,
                                        right=vehicle_stops_df,
                                        how="left")

    # calculate the distance from [person_prefix]_lat, [person_prefix]_lon, and the stop
    fasttrips.Util.calculate_distance_miles(person_trips_by_stops_df,
                                            origin_lat="%s_lat" % person_prefix, origin_lon="%s_lon" % person_prefix,
                                            destination_lat="stop_lat",          destination_lon="stop_lon",
                                            distance_colname="%s_stop_dist" % person_prefix)

    # get the closest stop
    fasttrips.FastTripsLogger.debug("person_trips_by_stops_df.head()=\n%s" % str(person_trips_by_stops_df.head()))
    person_stops_df = person_trips_by_stops_df.loc[ person_trips_by_stops_df.groupby("Unique_ID")["%s_stop_dist" % person_prefix].idxmin(),
        ["Unique_ID", "stop_id", "stop_name", "stop_lat", "stop_lon", "%s_stop_dist" % person_prefix] ]

    # rename the new columns
    person_stops_df.rename(columns={"stop_id"  :"%s_stop_id"   % person_prefix,
                                    "stop_name":"%s_stop_name" % person_prefix,
                                    "stop_lat" :"%s_stop_lat"  % person_prefix,
                                    "stop_lon" :"%s_stop_lon"  % person_prefix}, inplace=True)

    # put them back with the input
    person_trips_df = pd.merge(left     =person_trips_df,
                               right    =person_stops_df,
                               on       ="Unique_ID",
                               how      ="left",
                               indicator=True)

    # log what's failed (requires indicator to be True) and drop indicator
    missing_stop_ids = person_trips_df.loc[ person_trips_df["_merge"]=="left_only" ]
    if len(missing_stop_ids) > 0:
        fasttrips.FastTripsLogger.debug("missing stop ids:\n%s" % str(missing_stop_ids))
    person_trips_df.drop(["_merge"], axis=1, inplace=True)

    return person_trips_df

def add_trip_id(person_trips_df, veh_trips_df, include_route, hour_add):
    """
    Guesses at a trip id for the rows in the survey trips dataframe for the given operator, and adds it.
    """
    veh_trips_df = veh_trips_df[["service_id","mode","route_id","trip_id","stop_id","stop_sequence","departure_time_min"]].copy()
    # need to set a depart_hour to merge on time roughly too
    veh_trips_df["depart_hour"] = numpy.floor(veh_trips_df["departure_time_min"]/60.0)

    fasttrips.FastTripsLogger.debug("add_trip_id() person_trips_df.head()=\n%s" % str(person_trips_df.head()))
    fasttrips.FastTripsLogger.debug("add_trip_id() veh_trips_df.head()=\n%s" % str(veh_trips_df.head()))

    # maybe the vehicle departs in the following hour
    person_trips_df["veh depart_hour"] = person_trips_df["depart_hour"] + hour_add

    person_veh_df = {} # keep the person trips x vehicle trips here
    for stop_type in ["survey_board", "survey_alight"]:
        # see which trips qualify for the survey_board stop
        left_on_cols  = ["service_id","survey_mode","veh depart_hour","%s_stop_id" % stop_type]
        right_on_cols = ["service_id","mode",           "depart_hour","stop_id"]
        if include_route:
            left_on_cols.append("route_id")
            right_on_cols.append("route_id")

        fasttrips.FastTripsLogger.debug("add_trip_id() merging person_trips_df (%d) with veh_trips_df (%d) on %s==%s" % (len(person_trips_df), len(veh_trips_df), str(left_on_cols), str(right_on_cols)))
        person_veh_df[stop_type] = pd.merge(left     =person_trips_df[left_on_cols + ["Unique_ID"]],
                                            right    =veh_trips_df,
                                            left_on  =left_on_cols,
                                            right_on =right_on_cols,
                                            how      ="left",
                                            suffixes =[""," %s" % stop_type])
        # drop departure_time_min, depart_hour, stop_id (it's a dupe of survey_[board/alight]_stop_id), mode (dupe of survey_mode)
        person_veh_df[stop_type].drop(["departure_time_min","depart_hour","stop_id","mode","veh depart_hour"], axis=1, inplace=True)
        # rename stop sequence to be more specific
        person_veh_df[stop_type].rename(columns={"stop_sequence":"%s_stop_sequence" % stop_type}, inplace=True)
        fasttrips.FastTripsLogger.debug("done %d\n%s" % (len(person_veh_df[stop_type]), str(person_veh_df[stop_type].head())))

    # see if any of the trips are in common
    trips_df = pd.merge(left   =person_veh_df["survey_board"],
                        right  =person_veh_df["survey_alight"],
                        on     =["Unique_ID","service_id","survey_mode","route_id","trip_id"],
                        how    ="inner")
    fasttrips.FastTripsLogger.debug("trips %d\n%s" % (len(trips_df), str(trips_df.head())))
    # drop if sequence is out of order
    trips_df = trips_df.loc[ trips_df["survey_board_stop_sequence"]<trips_df["survey_alight_stop_sequence"] ]

    # there are likely multiple -- pick the first one
    trip_id_df = trips_df[["Unique_ID","service_id","survey_mode",
                           "route_id","trip_id","survey_board_stop_sequence","survey_alight_stop_sequence"]].groupby(["Unique_ID","service_id","survey_mode"]).agg(["first"])
    trip_id_df.columns = trip_id_df.columns.get_level_values(0) # flatten multiindex
    trip_id_df.reset_index(inplace=True)

    fasttrips.FastTripsLogger.debug("\n%s" % str(trip_id_df.head(10)))

    # join to return trip_id -- and overwrite route_id if we succeed
    person_trips_df = pd.merge(left    =person_trips_df,
                               right   =trip_id_df[["Unique_ID","route_id","trip_id","survey_board_stop_sequence","survey_alight_stop_sequence"]],
                               on      ="Unique_ID",
                               how     ="left",
                               suffixes=[""," trip"])

    person_trips_df.loc[ pd.notnull(person_trips_df["trip_id"]), "route_id"] = person_trips_df["route_id trip"]  # keep route_id for trip_id
    person_trips_df.drop(["route_id trip", "veh depart_hour"], axis=1, inplace=True)

    fasttrips.FastTripsLogger.debug("\n%s" % str(person_trips_df.head(10)))

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

    # Read the observed person trips file
    df = pd.read_csv('OBSdata_wBART_wSFtaz.csv',
                     dtype={"onoff_enter_station":object,
                            "onoff_exit_station":object,
                            "persons":object},
                     na_values=["None"])
    # Keep only the columns we're interested in
    df = df[[
        'Unique_ID',
        'operator',
        'transfer_from',         # operator
        'transfer_to',           # operator
        'access_mode',           'egress_mode',
        'route',
        'boardings',
        'survey_tech',           'survey_board_lat', 'survey_board_lon',
                                 'survey_alight_lat','survey_alight_lon',
        'first_board_tech',      'first_board_lat',  'first_board_lon',
        'last_alight_tech',      'last_alight_lat',  'last_alight_lon',
        'orig_maz',              'orig_sf_taz',
        'dest_maz',              'dest_sf_taz',
        'day_part',              'depart_hour',
        'weekpart',
        'onoff_enter_station',   'onoff_exit_station'
        ]]

    route_bridge    = pd.read_excel(OBS_to_GTFSPLUS,'operator_route-route')
    operator_bridge = pd.read_excel(OBS_to_GTFSPLUS,'operator-agency_service')
    tech_bridge     = pd.read_excel(OBS_to_GTFSPLUS,'tech-mode')

    # Add the agency_id and service_id to match the network data
    # Do this via join (rather than DataFrame.replace) so can log failures
    df = pd.merge(left     =df,
                  right    =operator_bridge,
                  on       ="operator",
                  how      ="left")
    # Summarize operator/agency_id/service_id
    fasttrips.FastTripsLogger.info("Summary of operator vs agency_id and service_id:\n%s" % \
                                   str(df[["Unique_ID","operator","agency_id","service_id"]].groupby(["operator","agency_id","service_id"]).agg(["count"])))
    missing_agency = df.loc[pd.isnull(df["agency_id"])]
    if len(missing_agency) > 0:
        fasttrips.FastTripsLogger.fatal("Didn't understand operators:\n%s" % str(missing_agency["operator"].value_counts()))
        sys.exit(2)

    # likewise, translate transfer_from and transfer_to operators to agency_id and service_id
    for xfer in ["transfer_from", "transfer_to"]:
        df = pd.merge(left     =df,
                      right    =operator_bridge,
                      left_on  =xfer,
                      right_on ="operator",
                      how      ="left",
                      suffixes =[""," %s" % xfer])
        df.drop(["operator %s" % xfer], axis=1, inplace=True) # dupe
        # Summarize xfer operator/agency_id/service_id
        fasttrips.FastTripsLogger.info("Summary of %s vs agency_id and service_id:\n%s" % \
            (xfer, str(df[["Unique_ID",xfer,"agency_id %s" % xfer,"service_id %s" % xfer]].groupby(
                                      [xfer,"agency_id %s" % xfer,"service_id %s" % xfer]).agg(["count"]))))
        missing_agency = df.loc[pd.isnull(df["agency_id %s" % xfer])&pd.notnull(df[xfer])]
        if len(missing_agency) > 0:
            fasttrips.FastTripsLogger.fatal("Didn't understand %s operators:\n%s" % (xfer, str(missing_agency[xfer].value_counts())))
            sys.exit(2)

    # OBS tech discrepency -- OBS calls amtrak "comuniter_rail" but the network has it as inter_regional_rail
    df.loc[ df["transfer_from"] =="AMTRAK", "first_board_tech"] = "inter_regional_rail"
    df.loc[ df["transfer_to"  ] =="AMTRAK", "last_alight_tech"] = "inter_regional_rail"

    # Add the survey mode to match network data
    df = pd.merge(left    =df,
                  right   =tech_bridge,
                  left_on ="survey_tech",
                  right_on="tech",
                  how      ="left")
    # Summarize tech/mode
    fasttrips.FastTripsLogger.info("Summary of survey_tech vs mode:\n%s" % \
                                   str(df[["Unique_ID","survey_tech","mode"]].groupby(["survey_tech","mode"]).agg(["count"])))
    df.rename(columns={"mode":"survey_mode"}, inplace=True)
    df.drop(["tech"], axis=1, inplace=True) # dupe

    # and for the transfers
    df = pd.merge(left    =df,
                  right   =tech_bridge,
                  left_on ="first_board_tech",
                  right_on="tech",
                  how     ="left")
    df.rename(columns={"mode":"first_board_mode"}, inplace=True)
    df.drop(["tech"], axis=1, inplace=True) # dupe

    df = pd.merge(left    =df,
                  right   =tech_bridge,
                  left_on ="last_alight_tech",
                  right_on="tech",
                  how     ="left")
    df.rename(columns={"mode":"last_alight_mode"}, inplace=True)
    df.drop(["tech"], axis=1, inplace=True) # dupe

    # Add the OBS_route to match the network data
    df["operator_route"] = df["operator"] + '_' + df["route"] #route dict reads data in the [operator]_[route] format
    # Caltrain and BART don't really have routes
    df.loc[ df["operator"]=="BART",     "operator_route" ] = df["operator"]
    df.loc[ df["operator"]=="Caltrain", "operator_route" ] = df["operator"]
    # do this with a join rather than a replace because we want to see where we fail to pickup the valid GTFS route
    route_df = pd.merge(left     =df,
                        right    =route_bridge,
                        on       ="operator_route",
                        how      ="left",
                        indicator=True)

    # make a more user-friendly version of _merge => route_id found
    route_df["route_id found"] = (route_df["_merge"] == "both")
    route_df.drop(["_merge"], axis=1, inplace=True)
    fasttrips.FastTripsLogger.info("Found route_id values:\n%s" % str(route_df["route_id found"].value_counts()))

    # write the route_id failures for follow-up
    route_count_df = route_df[["route_id found","agency_id","operator_route","Unique_ID"]].groupby(["route_id found","agency_id","operator_route"]).agg(["count"])
    route_count_df.columns = route_count_df.columns.get_level_values(0) # flatten multiindex
    route_count_df.rename(columns={"Unique_ID":"Unique_ID count"}, inplace=True)
    route_count_df.to_csv("route_id_failures.csv")
    fasttrips.FastTripsLogger.info("Wrote detail to route_id_failures.csv")

    # for trips with more than one route, need to pick one... pick the first one
    route_id_df = route_df[["Unique_ID","service_id","survey_mode","route_id"]].groupby(["Unique_ID","service_id","survey_mode"]).agg(["first"])
    route_id_df.columns = route_id_df.columns.get_level_values(0) # flatten multiindex
    route_id_df.reset_index(inplace=True)
    fasttrips.FastTripsLogger.info("len(route_id_df)=%d, head=\n%s" % (len(route_id_df), route_id_df.head()))

    # add it back to the primary df
    df = pd.merge(left =df,
                  right=route_id_df[["Unique_ID","route_id"]],
                  how  ="left")

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


    # This will print a few lines into the log so the columns are clear
    fasttrips.FastTripsLogger.info("observed person trips=\n%s" % str(df.head()))
    # These are the operators
    fasttrips.FastTripsLogger.info("operator value_counts()=\n%s" % str(df["operator"].value_counts()))

    # mark some lat/lons as invalid
    (min_stop_lat, max_stop_lat, min_stop_lon, max_stop_lon) = ft.stops.stop_min_max_lat_lon()
    for coord_type in ["survey_board", "survey_alight", "first_board", "last_alight"]:
        df["%s_invalid_coord" % coord_type] = False
        df.loc[ (df["%s_lat" % coord_type] < min_stop_lat-1.0)|
                (df["%s_lat" % coord_type] > max_stop_lat+1.0)|
                (df["%s_lon" % coord_type] < min_stop_lon-1.0)|
                (df["%s_lon" % coord_type] > max_stop_lon+1.0), "%s_invalid_coord" % coord_type ] = True
        fasttrips.FastTripsLogger.warn("Found %6d invalid coordinates for %s" % (df["%s_invalid_coord" % coord_type].sum(), coord_type))
        fasttrips.FastTripsLogger.debug("\n%s" % str(df.loc[df["%s_invalid_coord" % coord_type] == True]))

    # ===========================================================
    # process one service_id at a time, for memory reasons and debugging
    service_person_trips_all = pd.DataFrame()
    service_xferfr_trips_all = pd.DataFrame()
    service_xferto_trips_all = pd.DataFrame()

    service_id_set = set(df["service_id"].value_counts().keys()) | \
                     set(df["service_id transfer_from"].value_counts().keys()) | \
                     set(df["service_id transfer_to"].value_counts().keys())
    fasttrips.FastTripsLogger.info("all service_ids: %s" % str(service_id_set))
    for service_id in list(service_id_set):

        fasttrips.FastTripsLogger.info("======================== %s ========================" % service_id)

        # For BART and Caltrain, and also those where route_id is missing, we join on service_id only and not route_id,
        # for other operators, we join on both service_id and route_id, so that the stops are specific to the service + route.
        include_route = True
        if service_id == "bart_weekday" or service_id == "caltrain_weekday":
            include_route = False

        # select the possible vehicle trips for this service
        service_vehicle_trips = full_trips_df.loc[ full_trips_df["service_id"] == service_id ]
        fasttrips.FastTripsLogger.debug("service_vehicle_trips=\n%s" % str(service_vehicle_trips.head()))

        # first collect unique vehicle stops for the service
        service_unique_vehicle_stops = service_vehicle_trips[["service_id","mode","route_id","stop_id","stop_name","stop_lat","stop_lon"]].drop_duplicates()

        # map survey_board and survey_alight -- this adds the columns [survey_board,survey_alight]_[stop_id,stop_name,stop_lat,stop_lon,stop_dist]
        veh_stops = service_unique_vehicle_stops
        if not include_route:
            veh_stops = service_unique_vehicle_stops.drop(["route_id"], axis=1)


        ####################### select the observed person trips SURVEYED ON this service (with valid coords)
        service_person_trips  = df.loc[ (df["service_id"] == service_id)&
                                        (df["survey_board_invalid_coord"]==False)&
                                        (df["survey_alight_invalid_coord"]==False)]
        fasttrips.FastTripsLogger.debug("service_person_trips=\n%s" % str(service_person_trips.head()))

        service_person_trips = get_closest_stop(service_person_trips, veh_stops, "survey_board")
        service_person_trips = get_closest_stop(service_person_trips, veh_stops, "survey_alight")

        fasttrips.FastTripsLogger.info("Of %8d      OBS survey %30s rows, found %8d survey board stop ids and %8d survey alight stop ids" % \
            (len(service_person_trips), service_id,
             pd.notnull(service_person_trips["survey_board_stop_id"]).sum(),
             pd.notnull(service_person_trips["survey_alight_stop_id"]).sum()))

        # try to add a trip id from the possible vehicle trips
        service_person_trips = add_trip_id(service_person_trips, service_vehicle_trips, include_route=include_route, hour_add=0)
        # split into sucess and failure
        service_person_trips_success = service_person_trips[pd.notnull(service_person_trips["trip_id"])]
        service_person_trips_fail    = service_person_trips[pd.isnull(service_person_trips["trip_id"])].copy()

        service_person_trips_all = service_person_trips_all.append(service_person_trips_success)
        fasttrips.FastTripsLogger.info("                                                 (depart_hour+0)   and %8d trip_ids" % len(service_person_trips_success))

        # for fails, try the next hour
        service_person_trips_fail.drop(["trip_id","survey_board_stop_sequence","survey_alight_stop_sequence"], axis=1, inplace=True)
        service_person_trips = add_trip_id(service_person_trips_fail, service_vehicle_trips, include_route=include_route, hour_add=1)
        service_person_trips_all = service_person_trips_all.append(service_person_trips)
        fasttrips.FastTripsLogger.info("                                                 (depart_hour+1)   and %8d trip_ids" % pd.notnull(service_person_trips["trip_id"]).sum())

        ####################### select the observed person trips TRANSFERING FROM this service and with non-null first_board coords
        service_xferfr_trips  = df.loc[ (df["service_id transfer_from"] == service_id)&
                                        pd.notnull(df["first_board_lat"])&
                                        pd.notnull(df["first_board_lon"])&
                                        (df["first_board_invalid_coord"]==False),
                                       ["Unique_ID","service_id transfer_from","first_board_mode","first_board_lat","first_board_lon"]]
        service_xferfr_trips.rename(columns={"service_id transfer_from":"service_id",
                                             "first_board_mode":"mode"},
                                    inplace=True)

        # map first_board for trips that transfer_from this service
        service_xferfr_trips = get_closest_stop(service_xferfr_trips, service_unique_vehicle_stops, "first_board")

        fasttrips.FastTripsLogger.info("Of %8d   transfer_from %30s rows, found %8d first board stop ids" % \
            (len(service_xferfr_trips), service_id, pd.notnull(service_xferfr_trips["first_board_stop_id"]).sum()))
        service_xferfr_trips_all = service_xferfr_trips_all.append(service_xferfr_trips)


        ####################### select the observed person trips transfering to this service and with non-null last_alight coords
        service_xferto_trips  = df.loc[ (df["service_id transfer_to"] == service_id)&
                                        pd.notnull(df["last_alight_lat"])&
                                        pd.notnull(df["last_alight_lon"])&
                                        (df["last_alight_invalid_coord"]==False),
                                       ["Unique_ID","service_id transfer_to","last_board_mode","last_alight_lat","last_alight_lon"]]
        service_xferto_trips.rename(columns={"service_id transfer_to":"service_id",
                                             "last_alight_mode":"mode"},
                                    inplace=True)

        # map last_alight for trips that transfer_to this service
        service_xferto_trips = get_closest_stop(service_xferto_trips, service_unique_vehicle_stops, "last_alight")

        fasttrips.FastTripsLogger.info("Of %8d     transfer_to %30s rows, found %8d last alight stop ids" % \
            (len(service_xferto_trips), service_id, pd.notnull(service_xferto_trips["last_alight_stop_id"]).sum()))
        service_xferto_trips_all = service_xferto_trips_all.append(service_xferto_trips)

    # put together the main trips service_person_trips_all with the transfers
    df = pd.merge(left =service_person_trips_all,
                  right=service_xferto_trips_all[["Unique_ID","last_alight_stop_id","last_alight_stop_name","last_alight_stop_dist"]],
                  how  ="left",
                  on   ="Unique_ID")
    df = pd.merge(left =df,
                  right=service_xferfr_trips_all[["Unique_ID","first_board_stop_id","first_board_stop_name","first_board_stop_dist"]],
                  how  ="left")

    OUTFILE = "OBSdata_wBART_wSFtaz_wStops.csv"
    df.to_csv(OUTFILE, index=False)
    fasttrips.FastTripsLogger.info("Wrote %s" % OUTFILE)