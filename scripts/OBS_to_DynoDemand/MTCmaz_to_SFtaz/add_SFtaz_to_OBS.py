###################################################################################
# Converts MTC orig/dest maz's to SF taz's and adds them as two new columns to OBS file
# Reads: OBSdata_wBART.csv, mtcmaz_to_sftaz.csv
# Writes: OBSdata_wBART_wSFtaz.csv
##########################################################################################################
import pandas as pd
OBS = pd.read_csv('OBSdata_wBART.csv')
OBS = OBS.fillna(value='NA')
TAZ = pd.read_csv('mtcmaz_to_sftaz.csv')

OBS_mrg = pd.merge(OBS,TAZ,how='left',left_on=['orig_maz'],right_on=['MAZ'])
OBS_mrg.rename(columns={'TAZ':'orig_sf_taz'}, inplace=True)
OBS = OBS_mrg

OBS_mrg = pd.merge(OBS,TAZ,how='left',left_on=['dest_maz'],right_on=['MAZ'])
OBS_mrg.rename(columns={'TAZ':'dest_sf_taz'}, inplace=True)
OBS = OBS_mrg
OBS = OBS.drop(['MAZ_x','MAZ_y','cen_x_x','cen_x_y','cen_y_x','cen_y_y'],axis=1)
OBS.to_csv('OBSdata_wBART_wSFtaz.csv',index=False)
print 'Done'