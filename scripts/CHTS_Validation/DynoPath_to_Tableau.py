######################################################################################################
# Prepares DynoPath files from observed data source and FT model run to be compared in Tableau
# Reads: pathset_paths.csv and pathset_links.csv
# Writes: pathset_compare.csv
#######################################################################################################

import time, sys, os
sys.path.append("..")
from util_functions import *
import pandas as pd

start       = time.time()

OBS_DIR = r'Q:\Data\Surveys\HouseholdSurveys\CHTS2012\Data\W1_CHTS_GPS_Final_Data_Deliverable_Wearable'
MODEl_DIR = r'Q:\Model Development\SHRP2-fasttrips\Task4\CHTS_fasttrips_demand_v0.4_stochastic_iter1_nocap'
OUT_DIR = r'Q:\Model Development\SHRP2-fasttrips\Task4'
NETWORK_DIR = r'Q:\Model Development\SHRP2-fasttrips\Task2\built_fasttrips_network_2012Base\draft1.11_fare'
taz_corr_file = r'Y:\champ\dev\5.1.0_abmxfer\R_Summaries\data\taz_districts_sfcta.csv'

def prepDynoPath(dirpath):
    paths_df = pd.read_csv(os.path.join(dirpath, 'pathset_paths.csv'))
    links_df = pd.read_csv(os.path.join(dirpath, 'pathset_links.csv'))
    
    links_df.loc[links_df['mode']=='transit', 'mode'] = 'local_bus'
    paths_df = prim_mode_hierarchy(paths_df, links_df, 'primary_mode')
    
    return paths_df, links_df

obs_paths, obs_links = prepDynoPath(OBS_DIR)
mod_paths, mod_links = prepDynoPath(MODEl_DIR)

mod_chosen_links = mod_links.loc[mod_links['chosen']!='unchosen',]
mod_chosen_paths = mod_paths.loc[mod_paths['chosen']!='unchosen',]
mod_chosen_paths = mod_chosen_paths.rename(columns={'primary_mode':'mod_primary_mode'})
obs_paths = obs_paths.rename(columns={'primary_mode':'obs_primary_mode'})
compare_paths = obs_paths.merge(mod_chosen_paths[['person_id','person_trip_id','mod_primary_mode']], how='left')
compare_paths.loc[pd.isnull(compare_paths['mod_primary_mode']), 'mod_primary_mode'] = '9 None'

# get the origin TAZ and access stops
obs_links = obs_links.sort_values(['person_id','person_trip_id','linknum'])
temp_df = obs_links[['person_id','person_trip_id','A_id','B_id']].drop_duplicates(['person_id','person_trip_id'], keep='first')
temp_df = temp_df.rename(columns={'A_id':'o_taz', 'B_id':'obs_acc_stop'})
compare_paths = compare_paths.merge(temp_df, how='left')
mod_chosen_links = mod_chosen_links.sort_values(['person_id','person_trip_id','linknum'])
temp_df = mod_chosen_links[['person_id','person_trip_id','B_id']].drop_duplicates(['person_id','person_trip_id'], keep='first')
temp_df = temp_df.rename(columns={'B_id':'mod_acc_stop'})
compare_paths = compare_paths.merge(temp_df, how='left')

# get the destination TAZ and egress stops
temp_df = obs_links[['person_id','person_trip_id','A_id','B_id']].drop_duplicates(['person_id','person_trip_id'], keep='last')
temp_df = temp_df.rename(columns={'B_id':'d_taz', 'A_id':'obs_egr_stop'})
compare_paths = compare_paths.merge(temp_df, how='left')
temp_df = mod_chosen_links[['person_id','person_trip_id','A_id']].drop_duplicates(['person_id','person_trip_id'], keep='last')
temp_df = temp_df.rename(columns={'A_id':'mod_egr_stop'})
compare_paths = compare_paths.merge(temp_df, how='left')

# read in TAZ and stop coordinates
taz_coords = pd.read_csv(os.path.join(NETWORK_DIR, 'taz_coords.txt'))
taz_coords = taz_coords.set_index('taz')
stop_coords = pd.read_csv(os.path.join(NETWORK_DIR, 'stops.txt'))
stop_coords = stop_coords.set_index('stop_id')

compare_paths['obs_access_dist']=compare_paths[['o_taz','obs_acc_stop']].apply(get_dist, axis=1, args=(taz_coords,stop_coords))
compare_paths['mod_access_dist']=compare_paths[['o_taz','mod_acc_stop']].apply(get_dist, axis=1, args=(taz_coords,stop_coords))
compare_paths['obs_egress_dist']=compare_paths[['d_taz','obs_egr_stop']].apply(get_dist, axis=1, args=(taz_coords,stop_coords))
compare_paths['mod_egress_dist']=compare_paths[['d_taz','mod_egr_stop']].apply(get_dist, axis=1, args=(taz_coords,stop_coords))

# get the boarding time of the first transit leg
temp_df = obs_links.loc[obs_links['linkmode']=='transit',]
temp_df = temp_df[['person_id','person_trip_id','board_time']].drop_duplicates(['person_id','person_trip_id'], keep='first')
temp_df = temp_df.rename(columns={'board_time':'start_time'})
compare_paths = compare_paths.merge(temp_df, how='left')

taz_county_lookup = pd.read_csv(taz_corr_file)
taz_county_lookup = taz_county_lookup.set_index('TAZ')
compare_paths['o_county'] = compare_paths['o_taz'].map(taz_county_lookup['DISTRICT'])
compare_paths['d_county'] = compare_paths['d_taz'].map(taz_county_lookup['DISTRICT'])
COUNTY_DICT = {1:'1 San Francisco', 2:'2 San Mateo', 3:'3 Santa Clara', 4:'4 Alameda', 5:'5 Contra Costa', 6:'6 Solano',
               7:'7 Napa', 8:'8 Sonoma', 9:'9 Marin'}
compare_paths['o_county'] = compare_paths['o_county'].map(COUNTY_DICT)
compare_paths['d_county'] = compare_paths['d_county'].map(COUNTY_DICT) 

compare_paths['time_period'] = pd.Series(compare_paths['start_time']).apply(time_period)

outfile = os.path.join(OUT_DIR, 'pathset_compare.csv')
compare_paths = compare_paths.sort_values(['person_id','person_trip_id'])
compare_paths.to_csv(outfile, index=False)

print "Finished preparation in %5.2f mins" % ((time.time() - start)/60.0)
    
    

