######################################################################################################
# Prepares DynoPath files from observed data source and FT model run to be compared in Tableau
# Reads: pathset_paths.csv and pathset_links.csv
# Writes: pathset_compare.csv, xfer-links-obs.csv, xfer-links-mod.csv
#######################################################################################################

import time, sys, os
sys.path.append("..")
from util_functions import *
import pandas as pd

start       = time.time()

OBS_DIR = r'Q:\Data\Surveys\HouseholdSurveys\CHTS2012\Data\W1_CHTS_GPS_Final_Data_Deliverable_Wearable'
MODEl_DIR = r'Q:\Model Development\SHRP2-fasttrips\Task4\CHTS_fasttrips_demand_v0.4_stochastic_iter1_nocap'
OUT_DIR = r'Q:\Model Development\SHRP2-fasttrips\Task4\Output_Jayne_temp'
NETWORK_DIR = r'Q:\Model Development\SHRP2-fasttrips\Task2\built_fasttrips_network_2012Base\draft1.11_fare'
taz_corr_file = r'Y:\champ\dev\5.1.0_abmxfer\R_Summaries\data\taz_districts_sfcta.csv'

# read in TAZ and stop coordinates
taz_coords = pd.read_csv(os.path.join(NETWORK_DIR, 'taz_coords.txt'))
taz_coords = taz_coords.set_index('taz')
stop_coords = pd.read_csv(os.path.join(NETWORK_DIR, 'stops.txt'))
stop_coords = stop_coords.set_index('stop_id')

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

# get the boarding time of the first transit leg
temp_df = obs_links.loc[obs_links['linkmode']=='transit',]
temp_df = temp_df[['person_id','person_trip_id','board_time']].drop_duplicates(['person_id','person_trip_id'], keep='first')
temp_df = temp_df.rename(columns={'board_time':'start_time'})
compare_paths = compare_paths.merge(temp_df, how='left')

### access TAZs, time, and associated mode
obs_links = obs_links.sort_values(['person_id','person_trip_id','linknum'])
mod_chosen_links=mod_chosen_links.sort_values(['person_id','person_trip_id','linknum'])
temp_df = obs_links[['person_id','person_trip_id','A_id','B_id','mode','new_linktime_min']].drop_duplicates(['person_id','person_trip_id'], keep='first')
temp_df = temp_df.rename(columns={'A_id':'obs_o_tazA','B_id':'obs_o_tazB','mode':'obs_access_mode','new_linktime_min':'obs_acc_linktime'})

obs_links1=obs_links[obs_links['linknum']>0]
# the entry with the smallest linknum now is the first transit link
temp_df1 = obs_links1[['person_id','person_trip_id','mode']].drop_duplicates(['person_id','person_trip_id'], keep='first')
temp_df1 = temp_df1.rename(columns={'mode':'obs_mode_access_to'}) # mode of the first transit link

temp_df2= mod_chosen_links[['person_id','person_trip_id','A_id','B_id','mode','new_linktime min']].drop_duplicates(['person_id','person_trip_id'], keep='first')
temp_df2=temp_df2.rename(columns={'A_id':'mod_o_tazA','B_id':'mod_o_tazB','mode':'mod_access_mode','new_linktime min':'mod_acc_linktime'})

temp_df3 = mod_chosen_links[mod_chosen_links['linknum']>0]
temp_df3=temp_df3[['person_id','person_trip_id','mode']].drop_duplicates(['person_id','person_trip_id'], keep='first')
temp_df3=temp_df3.rename(columns={'mode':'mod_mode_access_to'})# mode of the first transit link

compare_paths = compare_paths.merge(temp_df, how='left')
compare_paths = compare_paths.merge(temp_df1, how='left')
compare_paths = compare_paths.merge(temp_df2, how='left')
compare_paths = compare_paths.merge(temp_df3, how='left')

### egress TAZs, time, and associated mode
obs_links_dest = obs_links.sort_values(['person_id','person_trip_id','linknum'],ascending = [True,True,False]).reset_index().drop('index',axis=1)
obs_links_dest['linknum'] = obs_links['linknum'] # now linknum is the smallest for the last link (egress has linknum = 0)
obs_links_dest1=obs_links_dest[obs_links_dest['linknum']>0] # drop the last link
temp_df = obs_links[['person_id','person_trip_id','A_id','B_id','mode','new_linktime_min']].drop_duplicates(['person_id','person_trip_id'], keep='last')
temp_df = temp_df.rename(columns={'A_id':'obs_d_tazA','B_id':'obs_d_tazB','mode':'obs_egress_mode','new_linktime_min':'obs_egr_linktime'})
temp_df1 = obs_links_dest1[['person_id','person_trip_id','mode']].drop_duplicates(['person_id','person_trip_id'], keep='first')
temp_df1 = temp_df1.rename(columns={'mode':'obs_mode_egress_from'}) # mode of the last transit link
temp_df2= mod_chosen_links[['person_id','person_trip_id','A_id','B_id','mode','new_linktime min']].drop_duplicates(['person_id','person_trip_id'], keep='last')
temp_df2=temp_df2.rename(columns={'A_id':'mod_d_tazA','B_id':'mod_d_tazB','mode':'mod_egress_mode','new_linktime min':'mod_egr_linktime'})# mode of the last transit link

mod_links_dest = mod_chosen_links.sort_values(['person_id','person_trip_id','linknum'],ascending = [True,True,False]).reset_index().drop('index',axis=1)
mod_links_dest['linknum']=mod_chosen_links['linknum']
mod_links_dest=mod_links_dest[mod_links_dest['linknum']>0]

temp_df3=mod_links_dest[['person_id','person_trip_id','mode']].drop_duplicates(['person_id','person_trip_id'], keep='first')
temp_df3=temp_df3.rename(columns={'mode':'mod_mode_egress_from'})

compare_paths = compare_paths.merge(temp_df, how='left')
compare_paths = compare_paths.merge(temp_df1, how='left')
compare_paths = compare_paths.merge(temp_df2, how='left')
compare_paths = compare_paths.merge(temp_df3, how='left')

compare_paths['obs_egr_linktime']=compare_paths['obs_egr_linktime'].replace(0,float('nan'))
compare_paths['obs_acc_linktime']=compare_paths['obs_acc_linktime'].replace(0,float('nan'))
compare_paths['mod_egr_linktime']=compare_paths['mod_egr_linktime'].replace(0,float('nan'))
compare_paths['mod_acc_linktime']=compare_paths['mod_acc_linktime'].replace(0,float('nan'))

# calculate access/egress distance
compare_paths['obs_access_dist']=compare_paths[['obs_o_tazA','obs_o_tazB']].apply(get_dist,axis=1)
compare_paths['mod_access_dist']=compare_paths[['mod_o_tazA','mod_o_tazB']].apply(get_dist,axis=1)
compare_paths['obs_egress_dist']=compare_paths[['obs_d_tazA','obs_d_tazB']].apply(get_dist,axis=1)
compare_paths['mod_egress_dist']=compare_paths[['mod_d_tazA','mod_d_tazB']].apply(get_dist,axis=1)
compare_paths.drop(['obs_o_tazB','mod_o_tazA','mod_o_tazB','obs_d_tazA','mod_d_tazA','mod_d_tazB'],axis=1,inplace=True)

compare_paths=compare_paths.rename(columns={'obs_o_tazA':'o_taz','obs_d_tazB':'d_taz'})






# origin/destination TAZ lookup
taz_county_lookup = pd.read_csv(taz_corr_file)
taz_county_lookup = taz_county_lookup.set_index('TAZ')
compare_paths['o_county'] = compare_paths['o_taz'].map(taz_county_lookup['DISTRICT'])
compare_paths['d_county'] = compare_paths['d_taz'].map(taz_county_lookup['DISTRICT'])
COUNTY_DICT = {1:'1 San Francisco', 2:'2 San Mateo', 3:'3 Santa Clara', 4:'4 Alameda', 5:'5 Contra Costa', 6:'6 Solano',
               7:'7 Napa', 8:'8 Sonoma', 9:'9 Marin'}
compare_paths['o_county'] = compare_paths['o_county'].map(COUNTY_DICT)
compare_paths['d_county'] = compare_paths['d_county'].map(COUNTY_DICT) 

compare_paths['time_period'] = pd.Series(compare_paths['start_time']).apply(time_period)




### higher level match
def num_of_transit_links_match(row):
    pID = row['person_id']
    ptID=row['person_trip_id']
    obs_links_table = obs_links[(obs_links['person_id'] == pID) & (obs_links['person_trip_id'] == ptID)]
    obs_num = len(obs_links_table[obs_links_table['linkmode']=='transit'])
    mod_links_table = mod_chosen_links[(mod_chosen_links['person_id'] == pID) & (mod_chosen_links['person_trip_id'] == ptID)]
    mod_num = len(mod_links_table[mod_links_table['linkmode']=='transit'])
    if obs_num == mod_num: return 1
    else: return 0
    
def links_to_path_str(df):
    path_str = ''
    df = df.sort_values(['linknum'])
    for i in df.index.values:
        path_str+=str(df.loc[i,'mode'])
        path_str+= ' '
        path_str+=str(df.loc[i,'A_id'])
        path_str+= ' '
        path_str+=str(df.loc[i,'B_id'])
        path_str+= ' '
        path_str+=str(df.loc[i,'route_id'])        
    return path_str

def obs_chosen_match(row):
    pID = row['person_id']
    ptID=row['person_trip_id']
    obs_links_table = obs_links[(obs_links['person_id'] == pID) & (obs_links['person_trip_id'] == ptID)]
    obs_str = links_to_path_str(obs_links_table)
    mod_links_table = mod_chosen_links[(mod_chosen_links['person_id'] == pID) & (mod_chosen_links['person_trip_id'] == ptID)]
    mod_str = links_to_path_str(mod_links_table)
    if obs_str == mod_str: return 1
    else: return 0
    
def obs_in_mod_result(row):
    pID = row['person_id']
    ptID=row['person_trip_id']
    obs_links_table = obs_links[(obs_links['person_id'] == pID) & (obs_links['person_trip_id'] == ptID)]
    obs_str = links_to_path_str(obs_links_table)
    mod_links_table = mod_links[(mod_links['person_id'] == pID) & (mod_links['person_trip_id'] == ptID)]
    if len(mod_links_table)==0: return 0
    else:
        num_mod_result = 1+max(mod_links_table['pathnum'])
        mod_path_list=[]
        for i in range(0,num_mod_result):
            path_table = mod_links_table[mod_links_table['pathnum']==i]
            mod_path_list.append(links_to_path_str(path_table))
        if obs_str in mod_path_list: return 1
        else: return 0


compare_paths['num_of_transit_links_match'] = compare_paths.apply(num_of_transit_links_match,axis=1)
# the results might be off probably due to empty mode / linkmode info in either the observed pathlinks or model outputs
compare_paths['obs_chosen_match'] = compare_paths.apply(obs_chosen_match,axis=1)
compare_paths['obs_in_mod_result'] = compare_paths.apply(obs_in_mod_result,axis=1)


### calculate primary mode by in-vehicle time
def route_id(row):
    if row['linkmode']=='transit':
        rID = row['route_id']
        if type(rID)==str:
            rID_cmpnt=rID.split('_')
            rID_sim=rID_cmpnt[-1]
            return rID_sim
            
def agency_id(row):
    if row['linkmode']=='transit':
        rID = row['route_id']
        if type(rID)==str:
            rID_cmpnt=rID.split('_')
            rID_sim=rID_cmpnt[-1]
            agency = rID.replace(rID_sim,'')[0:-1]
            return agency

def agency_match(row):
    if row['prim_mode_match']==True:
        if row['obs_agency_id']==row['mod_agency_id']: return 1
        else: return 0

def same_agency_route_match(row):
    if row['agency_match']==True:
        if row['obs_route_id']==row['mod_route_id']: return 1
        else: return 0

def same_route_endpoints_match(row):
    if row['same_agency_route_match']==True:
        if (row['obs_A_id']==row['mod_A_id']) & (row['obs_B_id']==row['mod_B_id']): return 1
        else: return 0
        
obs_links['in_veh_time']=obs_links.apply(get_inveh_time,axis=1)
mod_chosen_links['in_veh_time']=mod_chosen_links.apply(get_inveh_time,axis=1)

obs_links=obs_links.sort_values(['person_id','person_trip_id','in_veh_time'])
obs_links_transit = obs_links[obs_links['linkmode']=='transit'][['person_id','person_trip_id','in_veh_time','mode']].drop_duplicates(['person_id','person_trip_id'], keep='first')
temp_df=obs_links_transit.drop('in_veh_time',axis=1)
temp_df = temp_df.rename(columns={'mode':'prim_mode_by_time_obs'})
compare_paths = compare_paths.merge(temp_df, how='left')

mod_chosen_links=mod_chosen_links.sort_values(['person_id','person_trip_id','in_veh_time'])
mod_links_transit = mod_chosen_links[mod_chosen_links['linkmode']=='transit'][['person_id','person_trip_id','in_veh_time','mode']].drop_duplicates(['person_id','person_trip_id'], keep='first')
temp_df=mod_links_transit.drop(['in_veh_time'],axis=1)
temp_df = temp_df.rename(columns={'mode':'prim_mode_by_time_mod'})
compare_paths = compare_paths.merge(temp_df, how='left')

obs_links['route_id_simplified']=obs_links.apply(route_id,axis=1)
mod_chosen_links['route_id_simplified']=mod_chosen_links.apply(route_id,axis=1)
mod_chosen_links['agency_id']=mod_chosen_links.apply(agency_id,axis=1)

obs_links=obs_links.sort_values(['person_id','person_trip_id','in_veh_time'])
obs_links_transit = obs_links[obs_links['linkmode']=='transit'][['person_id','person_trip_id','agency_id','route_id_simplified','A_id','B_id']].drop_duplicates(['person_id','person_trip_id'], keep='first')
obs_links_transit=obs_links_transit.rename(columns={'agency_id':'obs_agency_id','route_id_simplified':'obs_route_id','A_id':'obs_A_id','B_id':'obs_B_id'})

mod_chosen_links=mod_chosen_links.sort_values(['person_id','person_trip_id','in_veh_time'])
mod_links_transit = mod_chosen_links[mod_chosen_links['linkmode']=='transit'][['person_id','person_trip_id','agency_id','route_id_simplified','A_id','B_id']].drop_duplicates(['person_id','person_trip_id'], keep='first')
mod_links_transit=mod_links_transit.rename(columns={'agency_id':'mod_agency_id','route_id_simplified':'mod_route_id','A_id':'mod_A_id','B_id':'mod_B_id'})

compare_paths=compare_paths.merge(obs_links_transit,how='left')
compare_paths=compare_paths.merge(mod_links_transit,how='left')

compare_paths['prim_mode_match']= (compare_paths['prim_mode_by_time_obs']==compare_paths['prim_mode_by_time_mod']).astype(int)
compare_paths['agency_match']=compare_paths.apply(agency_match,axis=1)
compare_paths['same_agency_route_match']=compare_paths.apply(same_agency_route_match,axis=1)
compare_paths['same_route_endpoints_match']=compare_paths.apply(same_route_endpoints_match,axis=1)

outfile = os.path.join(OUT_DIR, 'pathset_compare.csv')
compare_paths = compare_paths.sort_values(['person_id','person_trip_id'])
compare_paths.to_csv(outfile, index=False)


### transfer distance, link time and wait time
def get_transfer_A_id(row):
    mode=row['linkmode']
    index = row.reset_index().columns[1] # the number of row in the original dataframe
    if mode=='transfer':
        return obs_links.loc[index-1,'B_id']

def get_transfer_B_id(row):
    mode=row['linkmode']
    index = row.reset_index().columns[1]
    if mode=='transfer':
        return obs_links.loc[index+1,'A_id']

# fill transfer from and to modes in observed and modeled
def get_transfer_mode_from_obs(row):
    mode=row['linkmode']
    index = row.reset_index().columns[1]
    if mode=='transfer':
        return obs_links.loc[index-1,'mode']
    
def get_transfer_mode_from_mod(row):
    mode=row['linkmode']
    index = row.reset_index().columns[1]
    if mode=='transfer':
        return mod_chosen_links.loc[index-1,'mode']    

def get_transfer_mode_to_obs(row):
    mode=row['linkmode']
    index = row.reset_index().columns[1]
    if mode=='transfer':
        return obs_links.loc[index+1,'mode']
    
def get_transfer_mode_to_mod(row):
    mode=row['linkmode']
    index = row.reset_index().columns[1]
    if mode=='transfer':
        return mod_chosen_links.loc[index+1,'mode']    

# fill route ID from and to modes in observed and modeled
def get_routeID_from_obs(row):
    mode=row['linkmode']
    index = row.reset_index().columns[1]
    if mode=='transfer':
        return obs_links.loc[index-1,'route_id']
    
def get_routeID_from_mod(row):
    mode=row['linkmode']
    index = row.reset_index().columns[1]
    if mode=='transfer':
        return mod_chosen_links.loc[index-1,'route_id']

def get_routeID_to_obs(row):
    mode=row['linkmode']
    index = row.reset_index().columns[1]
    if mode=='transfer':
        return obs_links.loc[index+1,'route_id']
    
def get_routeID_to_mod(row):
    mode=row['linkmode']
    index = row.reset_index().columns[1]
    if mode=='transfer':
        return mod_chosen_links.loc[index+1,'route_id']    


obs_links['transfer_A_id']=obs_links.apply(get_transfer_A_id,axis=1)
obs_links['transfer_B_id']=obs_links.apply(get_transfer_B_id,axis=1)

obs_links['mode_from']=obs_links.apply(get_transfer_mode_from_obs,axis=1)
obs_links['mode_to']=obs_links.apply(get_transfer_mode_to_obs,axis=1)
mod_chosen_links['mode_from']=mod_chosen_links.apply(get_transfer_mode_from_mod,axis=1)
mod_chosen_links['mode_to']=mod_chosen_links.apply(get_transfer_mode_to_mod,axis=1)

obs_links['routeID_from']=obs_links.apply(get_routeID_from_obs,axis=1)
obs_links['routeID_to']=obs_links.apply(get_routeID_to_obs,axis=1)
mod_chosen_links['routeID_from']=mod_chosen_links.apply(get_routeID_from_mod,axis=1)
mod_chosen_links['routeID_to']=mod_chosen_links.apply(get_routeID_to_mod,axis=1)

wtime = obs_links['new_waittime_min'].sort_index()[1:]
wtime.index = wtime.index-1
wtime[len(wtime)]=float('nan')
obs_links['xfer_wait_time']=wtime

wtime  = mod_chosen_links['new_waittime min'].sort_index()[1:]
wtime.index = wtime.index-1
wtime[len(wtime)]=float('nan')
mod_chosen_links['xfer_wait_time']=wtime

obs_links_xfer = obs_links[obs_links['linkmode']=='transfer'][['person_id','person_trip_id','mode_from','mode_to','routeID_from','routeID_to','transfer_A_id','transfer_B_id','new_linktime_min','xfer_wait_time']]
mod_links_xfer = mod_chosen_links[mod_chosen_links['linkmode']=='transfer'][['person_id','person_trip_id','mode_from','mode_to','routeID_from','routeID_to','A_id','B_id','new_linktime min','xfer_wait_time']]
obs_links_xfer=obs_links_xfer.rename(columns={'new_linktime_min':'linktime'})
mod_links_xfer=mod_links_xfer.rename(columns={'A_id':'transfer_A_id','B_id':'transfer_B_id','new_linktime min':'linktime'})


# calculate transfer distance
obs_links_xfer['transfer_dist']=obs_links_xfer[['transfer_A_id','transfer_B_id']].apply(get_dist,axis=1)
mod_links_xfer['transfer_dist']=mod_links_xfer[['transfer_A_id','transfer_B_id']].apply(get_dist,axis=1)

pathmatch = compare_paths[['person_id','person_trip_id','obs_chosen_match']]
obs_links_xfer = obs_links_xfer.merge(pathmatch, on = ['person_id','person_trip_id'],how = 'left')
mod_links_xfer = mod_links_xfer.merge(pathmatch, on = ['person_id','person_trip_id'],how = 'left')


outfile = os.path.join(OUT_DIR, 'xfer-links-obs.csv')
obs_links_xfer = obs_links_xfer.sort_values(['person_id','person_trip_id'])
obs_links_xfer.to_csv(outfile, index=False)

outfile = os.path.join(OUT_DIR, 'xfer-links-mod.csv')
mod_links_xfer = mod_links_xfer.sort_values(['person_id','person_trip_id'])
mod_links_xfer.to_csv(outfile, index=False)


print "Finished preparation in %5.2f mins" % ((time.time() - start)/60.0)
    
    

