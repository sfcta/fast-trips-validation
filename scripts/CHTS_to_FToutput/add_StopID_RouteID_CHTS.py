###################################################################################
# Finds corresponding stop_id for A node/B node in CHTS_FToutput.csv.
# Reads: CHTS_FToutput.csv
# Writes: CHTS_FToutput_wStops_wRoutes.csv
####################################################################################
import pandas as pd
import fasttrips
NETWORK_DIR = r"C:\Code\fast-trips\Examples\sfcta\network_draft1.10_fare"

# bridge from CHTS travel_mode => operator_type
CHTS_MODE_TO_OPERATOR_TYPE = {
    15 : "Local_bus/Rapid_bus",
    16 : "GoldenGate/AC_transit",
    19 : None,
    20 : "AirBART",
    24 : "BART",
    23 : "Local_bus/Rapid_bus",
    25 : "ACE/Caltrain",
    26 : "MuniMetro/VTA",
    27 : "Street_car/Cable_car",
    29 : "Ferry"
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
max_dist = 0.25 # max distance for stop_id matching based on stops' lat/lon

def get_closest_stop(person_trips_df, vehicle_stops_df, location_prefix):
    # join the person trips with the stops
    person_trips_df = pd.merge(left=person_trips_df,
                                        right=vehicle_stops_df,
                                        how="inner")

    # calculate the distance from [location_prefix]_lat, [location_prefix]_lon, and the stop
    fasttrips.Util.calculate_distance_miles(person_trips_df,
                                            origin_lat="%s_lat" % location_prefix, origin_lon="%s_lon" % location_prefix,
                                            destination_lat="stop_lat",            destination_lon="stop_lon",
                                            distance_colname="stop_dist")

    # get the stops that are within a user defined range
    person_trips_df = person_trips_df[person_trips_df['stop_dist'] < max_dist]
    person_trips_df = person_trips_df.sort_values(['Unique_ID','route_id','agency_id','stop_dist'])
    person_trips_df = person_trips_df.groupby(['Unique_ID','route_id']).head(1)

    # rename the new columns
    person_trips_df.rename(columns={"stop_id"   :"%s_stop_id"   % location_prefix,
                                    "stop_name" :"%s_stop_name" % location_prefix,
                                    "stop_lat"  :"%s_stop_lat"  % location_prefix,
                                    "stop_lon"  :"%s_stop_lon"  % location_prefix,
                                    "stop_dist" :"%s_stop_dist" % location_prefix,
                                    "route_id"  :"%s_route_id"  % location_prefix,
                                    "agency_id" :"%s_agency_id"  % location_prefix}, inplace=True)
    return person_trips_df

if __name__ == "__main__":
    ft = fasttrips.FastTrips(input_network_dir= NETWORK_DIR,
                             input_demand_dir = None,
                             output_dir       = ".")
 
    ft.read_input_files()
    # Get the full (joined) transit vehicle trip table and add lat/lon for the stops
    full_trips_df = ft.trips.get_full_trips()
    full_trips_df = ft.stops.add_stop_lat_lon(full_trips_df, id_colname="stop_id", new_lat_colname="stop_lat", new_lon_colname="stop_lon", new_stop_name_colname="stop_name")
    # Add operator_type as the mutual field between CHTS and GTFS vehicle trips
    full_trips_df["operator_type"] = full_trips_df["agency_id"].replace(NETWORK_AGENCY_TO_OPERATOR_TYPE)

    # Read CHTS observed person trips file
    df = pd.read_csv('CHTS_ft_output.csv')
    # Add operator_type as the mutual field between CHTS and GTFS vehicle trips
    df["operator_type"] = df["transit_mode_no"].replace(CHTS_MODE_TO_OPERATOR_TYPE)
    # Add Unique_ID to be used for merging later on
    df['Unique_ID'] = df.index
    
    Locations = ['A','B']
    A_stops = pd.DataFrame()
    B_stops = pd.DataFrame()
    
    df_operator_type_series = df["operator_type"].value_counts()
    for OPtype in df_operator_type_series.keys():
        service_vehicle_trips = full_trips_df.loc[ full_trips_df["operator_type"] == OPtype ]
        # sf_muni has 3 different operation types: local bus, light rail and streetcar, 
        # So, whenever we are processing one of these operator types, we have to add sf_muni to service_vehicle_trips separately.
        if OPtype in muni_operations:
            muni_vehicle_trips = full_trips_df.loc[ full_trips_df["operator_type"] == 'sf_muni' ]
            # rename 'sf_muni' operator_type to OPtype being processed to be matchable with service_person_trips
            muni_vehicle_trips["operator_type"] = OPtype
            # add sf_muni trips to service_vehicle_trips
            service_vehicle_trips = service_vehicle_trips.append(muni_vehicle_trips)
        service_person_trips  = df.loc[ df["operator_type"] == OPtype ]
    
        print OPtype
        service_unique_vehicle_stops = service_vehicle_trips[["operator_type","agency_id","route_id","stop_id","stop_name","stop_lat","stop_lon"]].drop_duplicates()
        for i in Locations:
            stops = get_closest_stop(service_person_trips, service_unique_vehicle_stops, i)
            stops = stops[['Unique_ID', i+'_stop_id', i+'_stop_name', i+'_stop_lat', i+'_stop_lon', i+'_route_id', i+'_agency_id', i+'_stop_dist']]
            if   i=='A'  : 
                A_stops  = A_stops.append(stops, ignore_index=True)
            else         : 
                B_stops  = B_stops.append(stops, ignore_index=True)


    # Put all stop_id and route_id info into the original CHTS dataframe
    new_df = df
    new_df = pd.merge (new_df, A_stops, how='left', on='Unique_ID')
    new_df = pd.merge (new_df, B_stops, how='left', on='Unique_ID')
    new_df['sum_dist'] = new_df['A_stop_dist'] + new_df['B_stop_dist']
    # first, pick out the records for which A_route_id and B_route_id are the same
    # ideally, all records should fall in this category since each record is a single unlinked transit trip
    screen_uids = new_df.loc[(new_df['A_route_id']==new_df['B_route_id']) & (pd.notnull(new_df['A_route_id'])), 'Unique_ID'].unique()
    new_df1 = new_df.loc[new_df['Unique_ID'].isin(screen_uids),]
    new_df1 = new_df.loc[(new_df['A_route_id']==new_df['B_route_id']) & (pd.notnull(new_df['A_route_id'])),]
    new_df1 = new_df1.groupby(['Unique_ID']).head(1)
    
    # now, deal with the records for which the A and B routes don't match. It appears like BART transfers are not being detected by GPS in some cases
    # we will just minimize the sum of distances to potential transit stops matches on both ends
    new_df = new_df.loc[new_df['Unique_ID'].isin(screen_uids)==False,]
    new_df = new_df.sort_values(['Unique_ID','sum_dist'])
    new_df = new_df.groupby(['Unique_ID']).head(1)

    # combine both dataframes
    new_df = new_df.append(new_df1)
    
    #A_id in access links and B_id in egress links should be taz_id and not stop_id
    # however, mapping to TAZ will be done offline by SFCTA using coordinated and TAZ shapefile  

    new_df = new_df.sort_values(['Unique_ID'])
    new_df.to_csv("CHTS_FToutput_wStops_wRoutes.csv", index=False)
    print 'Done'