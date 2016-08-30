######################################################################################################
# Finds corresponding stop_id's for boarding/alighting locations in OBS file by matching stops' lat/long
# Reads: OBSdata_wBART_wSFtaz.csv, stops.txt
# Writes: OBSdata_wBART_wSFtaz_wStops.csv
#######################################################################################################
import pandas as pd
df = pd.read_csv('OBSdata_wBART_wSFtaz.csv')
#Removing unnecessary columns
df = df[['operator','Unique_ID','ID','access_mode','egress_mode','route','boardings','survey_tech','first_board_tech','last_alight_tech','transfer_from','transfer_to','first_board_lat','first_board_lon','survey_board_lat','survey_board_lon','survey_alight_lat','survey_alight_lon','last_alight_lat','last_alight_lon','orig_maz','orig_sf_taz','dest_maz','dest_sf_taz']]

stops = pd.read_csv('stops.txt')
stops = stops.drop(['stop_name','zone_id'],axis=1)
#Reducing the number of digits in lat/lon coordinates
digits = 3
for i in range(len(stops)):
    stops.loc[i,'stop_lat'] = round(stops.loc[i,'stop_lat'],digits)
    stops.loc[i,'stop_lon'] = round(stops.loc[i,'stop_lon'],digits)
    #stops['stop_lat'][i] = round(stops['stop_lat'][i],digits)

Locations = ['first_board','survey_board','survey_alight','last_alight']
person_id = []
for i in range(len(df)):
    for j in Locations:
        df.loc[i,j+'_lat'] = round(df.loc[i,j+'_lat'],digits)
        df.loc[i,j+'_lon'] = round(df.loc[i,j+'_lon'],digits)
    person_id.append('hh' + str(i+1) + '_' + str(df['ID'][i]))
df.insert(0,'person_id',person_id)

for j in Locations:
    df_mrg = pd.merge(df,stops,how='left',left_on=[j+'_lat', j+'_lon'],right_on=['stop_lat', 'stop_lon'])
    df_mrg.rename(columns={'stop_id' : j+'_stop'}, inplace=True)
    df = df_mrg
    
df.drop_duplicates(['person_id'],inplace=True)
df = df.drop(['stop_lat_x','stop_lon_x','stop_lat_y','stop_lon_y'],axis=1)
df = df.reset_index(drop=True)
df.to_csv('OBSdata_wBART_wSFtaz_wStops.csv',index=False)
print 'Done'