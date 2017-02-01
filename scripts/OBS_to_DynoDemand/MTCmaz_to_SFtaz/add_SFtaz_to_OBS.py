###################################################################################
# Converts MTC orig/dest maz's to SF taz's and adds them as two new columns to OBS file
# Reads: survey.csv, mtcmaz_to_sftaz.csv
# Writes: survey_wSFtaz.csv
##########################################################################################################
import pandas as pd
OBS = pd.read_csv('survey.csv',
                  dtype={"onoff_enter_station":object,
                         "onoff_exit_station" :object,
                         "persons"            :object,
                         "ID"                 :object,
                         "approximate_age"    :object,
                         "depart_hour"        :object,
                         "return_hour"        :object},
                  na_values=["missing"])
TAZ = pd.read_csv('mtcmaz_to_sftaz.csv')

OBS_mrg = pd.merge(OBS,TAZ,how='left',left_on=['orig_maz'],right_on=['MAZ'])
OBS_mrg.rename(columns={'TAZ':'orig_sf_taz'}, inplace=True)
OBS = OBS_mrg

OBS_mrg = pd.merge(OBS,TAZ,how='left',left_on=['dest_maz'],right_on=['MAZ'])
OBS_mrg.rename(columns={'TAZ':'dest_sf_taz'}, inplace=True)
OBS = OBS_mrg
OBS = OBS.drop(['MAZ_x','MAZ_y','cen_x_x','cen_x_y','cen_y_x','cen_y_y'],axis=1)
OBS.to_csv('survey_wSFtaz.csv',index=False)
print 'Done'