import pandas as pd
import os

work_dir = r'Q:\Data\Surveys\HouseholdSurveys\CHTS2012\Data\W1_CHTS_GPS_Final_Data_Deliverable_Wearable'
infile = 'CHTS_FToutput_wStops_wRoutes.csv'
tazmapfile = 'CHTS_FToutput_wTAZ.csv'
outfile = 'CHTS_FToutput_wStopsRoutesTAZ.csv'

# bridge from stop_id to taz_id
taz_dict = pd.read_csv(r'C:\Code\fast-trips-validation\data\nodesToTAZ.csv')
taz_dict = taz_dict[['N','TAZ']]

gps_df = pd.read_csv(os.path.join(work_dir, infile))
taz_df = pd.read_csv(os.path.join(work_dir, tazmapfile))
taz_df['A_id'] = taz_df['A_stop_id']
taz_df['B_id'] = taz_df['B_stop_id']
taz_df.loc[taz_df['linkmode']=='access', 'A_id'] = taz_df.loc[taz_df['linkmode']=='access', 'A_TAZ']
taz_df.loc[taz_df['linkmode']=='egress', 'B_id'] = taz_df.loc[taz_df['linkmode']=='egress', 'B_TAZ']

taz_df = taz_df[list(gps_df.columns) + ['A_id','B_id']]
taz_df = taz_df.drop(['A_lat','A_lon','B_lat','B_lon'], axis=1)

taz_df = taz_df.sort_values(['Unique_ID'])
taz_df.to_csv(os.path.join(work_dir, outfile), index=False)
print 'Done'

