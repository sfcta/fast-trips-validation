import pandas as pd
import os

work_dir = r'Q:\Data\Surveys\HouseholdSurveys\CHTS2012\Data\W1_CHTS_GPS_Final_Data_Deliverable_Wearable'
infile = 'CHTS_FToutput_wTAZ.csv'
outfile_links = 'CHTS_FToutput_links.csv'
outfile_paths = 'CHTS_FToutput_paths.csv'

# This runs in two modes
# mode 1: create dyno-path links file
# mode 2: create dyno-path paths file
RUNMODE = 2

# bridge from stop_id to taz_id
taz_dict = pd.read_csv(r'C:\Code\fast-trips-validation\data\nodesToTAZ.csv')
taz_dict = taz_dict[['N','TAZ']]

if RUNMODE==1:
    path_links_df = pd.read_csv(os.path.join(work_dir, infile))
    path_links_df['A_id'] = path_links_df['A_stop_id']
    path_links_df['B_id'] = path_links_df['B_stop_id']
    path_links_df.loc[path_links_df['linkmode']=='access', 'A_id'] = path_links_df.loc[path_links_df['linkmode']=='access', 'A_TAZ']
    path_links_df.loc[path_links_df['linkmode']=='egress', 'B_id'] = path_links_df.loc[path_links_df['linkmode']=='egress', 'B_TAZ']
#     path_links_df = path_links_df.drop(['A_lat','A_lon','B_lat','B_lon'], axis=1)
    
    path_links_df.rename(columns={'trip_list_id_num':'person_trip_id',
                                  'A_route_id':'route_id',
                                  'A_agency_id':'agency_id'}, inplace=True)
    path_links_df['A_seq'] = ""
    path_links_df['B_seq'] = ""
    path_links_df['service_id'] = ""
    path_links_df['trip_id'] = ""
    path_links_df = path_links_df[['person_id','person_trip_id','linkmode','A_id','A_seq','B_id','B_seq','linknum','mode','route_id','trip_id','agency_id','service_id','board_time','alight_time']]

    path_links_df.sort_values(by=["person_id","person_trip_id","linknum"], inplace=True)
    path_links_df.to_csv(os.path.join(work_dir, outfile_links), index=False)

elif RUNMODE==2:
    
    df = pd.read_csv(r'Q:\Model Development\SHRP2-fasttrips\Task3\chts_demand_conversion\version_0.4\trip_list.txt',sep=',',
                               dtype={"person_trip_id":object})
    # add dyno-path columns
    df["pathdir"] = 1  # outbound (time_target=arrival)
    df.loc[df["time_target"]=="departure", "pathdir"] = 2 # inbound (time_target=departure)
    df.rename(columns={"mode":"pathmode"}, inplace=True)
    # keep only the columns we want and output paths
    df = df[['person_id','person_trip_id','pathdir','pathmode']]
    df.sort_values(by=["person_id","person_trip_id"], inplace=True)
    df.to_csv(os.path.join(work_dir, outfile_paths),index=False)
     
    
    path_links_df = pd.read_csv(os.path.join(work_dir, outfile_links), dtype={"person_trip_id":object})
    path_links_df = path_links_df.loc[(path_links_df['person_id']).isin(df['person_id']) & (path_links_df['person_trip_id']).isin(df['person_trip_id']),]
    path_links_df.sort_values(by=["person_id","person_trip_id","linknum"], inplace=True)
    path_links_df.to_csv(os.path.join(work_dir, outfile_links), index=False)
    

print 'Done'

