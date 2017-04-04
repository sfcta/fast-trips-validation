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
    
    # fill in B_id and A_id for access and egress links respectively
    access_links = path_links_df.loc[path_links_df['linkmode']=='access',['person_id','person_trip_id','linknum']]
    access_links['linknum'] += 1
    access_links = access_links.merge(path_links_df[['person_id','person_trip_id','linknum','A_stop_id']], 
                                      on=['person_id','person_trip_id','linknum'], how='left')
    access_links = access_links[['person_id','person_trip_id','linknum','A_stop_id']]
    access_links = access_links.rename(columns={'A_stop_id':'A_access'})
    access_links['linknum'] -= 1
    
    egr_links = path_links_df.loc[path_links_df['linkmode']=='egress',['person_id','person_trip_id','linknum']]
    egr_links['linknum'] -= 1
    egr_links = egr_links.merge(path_links_df[['person_id','person_trip_id','linknum','B_stop_id']], 
                                      on=['person_id','person_trip_id','linknum'], how='left')
    egr_links = egr_links[['person_id','person_trip_id','linknum','B_stop_id']]
    egr_links = egr_links.rename(columns={'B_stop_id':'B_egress'})
    egr_links['linknum'] += 1
    
    path_links_df = path_links_df.merge(access_links, how='left')
    path_links_df = path_links_df.merge(egr_links, how='left')
    path_links_df.loc[path_links_df['linkmode']=='access', 'B_id'] = path_links_df.loc[path_links_df['linkmode']=='access', 'A_access']
    path_links_df.loc[path_links_df['linkmode']=='egress', 'A_id'] = path_links_df.loc[path_links_df['linkmode']=='egress', 'B_egress']
    
    # add remaining variables and output
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
    path_links_df.loc[pd.isnull(path_links_df['A_id']), 'A_id'] = 0
    path_links_df.loc[pd.isnull(path_links_df['B_id']), 'B_id'] = 0
    path_links_df[['A_id','B_id']] = path_links_df[['A_id','B_id']].astype(int)
    path_links_df.to_csv(os.path.join(work_dir, outfile_links), index=False)
    

print 'Done'

