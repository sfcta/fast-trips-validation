######################################################################################################
# Prepares DynoPath files from observed data source and FT model run to be compared in Tableau
# Reads: pathset_paths.csv and pathset_links.csv
# Writes: pathset_compare.csv, xfer-links-obs.csv, xfer-links-mod.csv
#######################################################################################################

import time, sys, os
sys.path.append("..")
from util_functions import *
import pandas as pd
import numpy as np

start       = time.time()

OBS_DIR = r'Q:\Data\Surveys\HouseholdSurveys\CHTS2012\Data\W1_CHTS_GPS_Final_Data_Deliverable_Wearable'
MODEl_DIR = r'C:\Code\fast-trips\Examples\sfcta\output\Run7.1'
OUT_DIR = r'Q:\Model Development\SHRP2-fasttrips\Task4\ft_output'
NETWORK_DIR = r'Q:\Model Development\SHRP2-fasttrips\Task2\built_fasttrips_network_2012Base\draft1.14_fare'
taz_corr_file = r'Y:\champ\dev\5.1.0_abmxfer\R_Summaries\data\taz_districts_sfcta.csv'

# read in TAZ and stop coordinates
taz_coords = pd.read_csv(os.path.join(NETWORK_DIR, 'taz_coords.txt'))
taz_coords = taz_coords.set_index('taz')
stop_coords = pd.read_csv(os.path.join(NETWORK_DIR, 'stops.txt'))
stop_coords = stop_coords.set_index('stop_id')

def prepDynoPath(dirpath, out_flag=False):
    paths_df = pd.read_csv(os.path.join(dirpath, 'pathset_paths.csv'))
    links_df = pd.read_csv(os.path.join(dirpath, 'pathset_links.csv'))
    
    paths_df = paths_df.loc[paths_df.groupby(['person_id','person_trip_id','pathnum'])['pathfinding_iteration'].idxmax(),]
    links_df = links_df.loc[links_df.groupby(['person_id','person_trip_id','pathnum','linknum'])['pathfinding_iteration'].idxmax(),]
    
    if out_flag:
        paths_df.to_csv(os.path.join(OUT_DIR, 'pathset_paths.csv'), index=False)
        links_df.to_csv(os.path.join(OUT_DIR, 'pathset_links.csv'), index=False)
    
    links_df.loc[links_df['mode']=='transit', 'mode'] = 'local_bus'
    paths_df = prim_mode_hierarchy(paths_df, links_df, 'primary_mode')
    
    return paths_df, links_df

obs_paths, obs_links = prepDynoPath(OBS_DIR)
mod_paths, mod_links = prepDynoPath(MODEl_DIR, True)


obs_paths = obs_paths.rename(columns={'primary_mode':'obs_primary_mode'})
# filter out no-path records in obs data
noobs = obs_paths.loc[obs_paths['obs_primary_mode']=='9 None',]
obs_paths = filterby_pid(noobs, obs_paths)
# filter out paths with not even one route_id identified
obs_links['rtecount'] = np.where(pd.notnull(obs_links['route_id']), 1, 0)
no_rteid = obs_links[['person_id','person_trip_id','pathnum','rtecount']].groupby(['person_id','person_trip_id','pathnum']).sum().reset_index()
no_rteid = no_rteid.loc[no_rteid['rtecount']==0,]
obs_paths = filterby_pid(no_rteid, obs_paths)
obs_links = obs_links.drop('rtecount', 1)
# filter out paths with bike access or egress
obs_links['bike_flag'] = 0
obs_links.loc[obs_links['mode'].isin(['bike_access','bike_egress']),'bike_flag'] = 1
bike_acc = obs_links[['person_id','person_trip_id','pathnum','bike_flag']].groupby(['person_id','person_trip_id','pathnum']).sum().reset_index()
bike_acc = bike_acc.loc[bike_acc['bike_flag']>0,]
obs_paths = filterby_pid(bike_acc, obs_paths)
obs_links = obs_links.drop('bike_flag', 1)

mod_paths = mod_paths.rename(columns={'primary_mode':'mod_primary_mode'})
mod_chosen_links = mod_links.loc[(~mod_links['chosen'].isin(['unchosen','rejected'])) & (pd.notnull(mod_links['chosen'])),]
mod_chosen_paths = mod_paths.loc[(~mod_paths['chosen'].isin(['unchosen','rejected'])) & (pd.notnull(mod_paths['chosen'])) ,]

compare_paths = obs_paths.merge(mod_chosen_paths[['person_id','person_trip_id','mod_primary_mode']], how='left')
compare_paths.loc[pd.isnull(compare_paths['mod_primary_mode']), 'mod_primary_mode'] = '9 None'

# get the boarding time of the first transit leg
temp_df = obs_links.loc[obs_links['linkmode']=='transit',]
temp_df = temp_df[['person_id','person_trip_id','board_time']].drop_duplicates(['person_id','person_trip_id'], keep='first')
temp_df = temp_df.rename(columns={'board_time':'start_time'})
compare_paths = compare_paths.merge(temp_df, how='left')

### OD TAZs
temp_df = get_path_attrs(obs_links, ['A_id'], ['o_taz'], keep='first')
compare_paths = compare_paths.merge(temp_df, how='left')
temp_df = get_path_attrs(obs_links, ['B_id'], ['d_taz'], keep='last')
compare_paths = compare_paths.merge(temp_df, how='left')
# remove any intra-taz trips from comparison
compare_paths = compare_paths.loc[compare_paths['o_taz']!=compare_paths['d_taz'],]

### access/egress time, and distance
dfs = [obs_links, mod_chosen_links]
sources = ['obs','mod']
for src,df in zip(sources,dfs):
    for typ,k,c,t in zip(['acc','egr'],['first','last'],['B_id','A_id'],['o_taz','d_taz']):
        time_col = 'new_linktime_min' if 'new_linktime_min' in df.columns else 'new_linktime min'
        temp_df = get_path_attrs(df, [c,time_col], ['%s_%s_stp' %(src,typ),'%s_%s_time' %(src,typ)], keep=k)
        compare_paths = compare_paths.merge(temp_df, how='left')
        compare_paths['%s_%s_dist' %(src,typ)]=compare_paths[[t,'%s_%s_stp' %(src,typ)]].apply(get_dist,axis=1,args=(taz_coords,stop_coords))

for src,df in zip(sources,dfs):
    ### calculate total xfer time and distance for each path
    temp_df = df.loc[df['linkmode']=='transfer',].reset_index()
    temp_df['xfer_dist'] = temp_df[['A_id','B_id']].apply(get_dist,axis=1,args=(taz_coords,stop_coords))
    temp_df['xfer_time'] = temp_df['new_linktime_min'] if 'new_linktime_min' in temp_df.columns else temp_df['new_linktime min']
    temp_df['xfer_count'] = 1
    temp_df = temp_df[['person_id','person_trip_id','xfer_count','xfer_time','xfer_dist']].groupby(['person_id','person_trip_id']).sum().reset_index()
    temp_df.columns = ['person_id','person_trip_id','%s_xfer_count' %src,'%s_xtrav_time' %src,'%s_xfer_dist' %src]
    compare_paths = compare_paths.merge(temp_df, how='left')
    compare_paths['%s_xfer_count' %src] = compare_paths['%s_xfer_count' %src].fillna(0)
    
    ### calculate total xfer wait time
    temp_df = df.loc[df['linknum'] > 1,].reset_index() # retain only links that are after the first transit link
    xfer_wait_col = 'new_waittime_min' if 'new_waittime_min' in temp_df.columns else 'new_waittime min'
    temp_df = temp_df[['person_id','person_trip_id','%s' %xfer_wait_col]].groupby(['person_id','person_trip_id']).sum().reset_index()
    temp_df.columns = ['person_id','person_trip_id','%s_xwait_time' %src]
    compare_paths = compare_paths.merge(temp_df, how='left')  
    ## total xfer time
    compare_paths['%s_xfer_time' %src] = compare_paths['%s_xtrav_time' %src] + compare_paths['%s_xwait_time' %src]

# obs paths with more than 3 transfers are probably not accurate
compare_paths = compare_paths.loc[compare_paths['obs_xfer_count']<4,]

### origin/destination TAZ lookup
taz_county_lookup = pd.read_csv(taz_corr_file)
taz_county_lookup = taz_county_lookup.set_index('TAZ')
compare_paths['o_county'] = compare_paths['o_taz'].map(taz_county_lookup['DISTRICT'])
compare_paths['d_county'] = compare_paths['d_taz'].map(taz_county_lookup['DISTRICT'])
COUNTY_DICT = {1:'1 San Francisco', 2:'2 San Mateo', 3:'3 Santa Clara', 4:'4 Alameda', 5:'5 Contra Costa', 6:'6 Solano',
               7:'7 Napa', 8:'8 Sonoma', 9:'9 Marin'}
compare_paths['o_county'] = compare_paths['o_county'].map(COUNTY_DICT)
compare_paths['d_county'] = compare_paths['d_county'].map(COUNTY_DICT)
compare_paths['od_market'] = '5 Other' 
compare_paths.loc[(compare_paths['d_county']=='1 San Francisco') & 
                  (compare_paths['o_county']=='1 San Francisco'), 'od_market'] = '1 Intra SF'
ebay_counties = ['4 Alameda', '5 Contra Costa','6 Solano','7 Napa']
compare_paths.loc[(compare_paths['d_county']=='1 San Francisco') & 
                  (compare_paths['o_county'].isin(ebay_counties)), 'od_market'] = '2 SF-East Bay'
compare_paths.loc[(compare_paths['o_county']=='1 San Francisco') & 
                  (compare_paths['d_county'].isin(ebay_counties)), 'od_market'] = '2 SF-East Bay' 
sbay_counties = ['2 San Mateo', '3 Santa Clara']
compare_paths.loc[(compare_paths['d_county']=='1 San Francisco') & 
                  (compare_paths['o_county'].isin(sbay_counties)), 'od_market'] = '3 SF-South Bay'
compare_paths.loc[(compare_paths['o_county']=='1 San Francisco') & 
                  (compare_paths['d_county'].isin(sbay_counties)), 'od_market'] = '3 SF-South Bay'  
nbay_counties = ['8 Sonoma', '9 Marin']
compare_paths.loc[(compare_paths['d_county']=='1 San Francisco') & 
                  (compare_paths['o_county'].isin(nbay_counties)), 'od_market'] = '4 SF-North Bay'
compare_paths.loc[(compare_paths['o_county']=='1 San Francisco') & 
                  (compare_paths['d_county'].isin(nbay_counties)), 'od_market'] = '4 SF-North Bay'                                                      

### assign time period
compare_paths['time_period'] = pd.Series(compare_paths['start_time']).apply(time_period)

### match flags
compare_paths['pm_match_flag'] = 0
compare_paths.loc[(compare_paths['obs_primary_mode']==compare_paths['mod_primary_mode']),'pm_match_flag'] = 1

# search for primary mode matches in FT pathset
unchosen_paths = mod_paths.loc[mod_paths['chosen'].isin(['unchosen','rejected']),]
unchosen_paths = unchosen_paths[['person_id','person_trip_id','mod_primary_mode','pathnum','probability']]
temp_df = compare_paths.loc[compare_paths['pm_match_flag']==0,['person_id','person_trip_id','obs_primary_mode']]
temp_df = temp_df.merge(unchosen_paths)
temp_df['ps_match_flag'] = 0
temp_df.loc[(temp_df['obs_primary_mode']==temp_df['mod_primary_mode']),'ps_match_flag'] = 1
temp_df = temp_df[['person_id','person_trip_id','ps_match_flag']].groupby(['person_id','person_trip_id']).sum().reset_index()
temp_df = unchosen_paths.merge(temp_df)
temp_df = temp_df.loc[temp_df['ps_match_flag']>0,]
temp_df = temp_df.sort_values(['person_id','person_trip_id','pathnum','probability'], ascending=[True,True,True,False])
temp_df = temp_df.drop_duplicates(['person_id','person_trip_id'], keep='first')
temp_df = temp_df[['person_id','person_trip_id','pathnum','probability']]
temp_df = temp_df.rename(columns={'pathnum':'pathnum_ps','probability':'prob_ps'})
compare_paths = compare_paths.merge(temp_df, how='left')
compare_paths['ps_match_flag'] = 0
compare_paths.loc[pd.notnull(compare_paths['pathnum_ps']),'ps_match_flag'] = 1

compare_paths['prim_mode_match'] = '3 Obs. path not in FT'
compare_paths.loc[compare_paths['mod_primary_mode']=='9 None','prim_mode_match'] = '4 No FT path found'
compare_paths.loc[compare_paths['ps_match_flag']==1,'prim_mode_match'] = '2 Obs. path in Pathset'
compare_paths.loc[compare_paths['pm_match_flag']==1,'prim_mode_match'] = '1 Obs. path = Chosen path'

outfile = os.path.join(OUT_DIR, 'pathset_compare.csv')
compare_paths = compare_paths.sort_values(['person_id','person_trip_id'])
compare_paths.to_csv(outfile, index=False)

### melted version for Tableau
# access distance
compare_paths_melt = melt_df(compare_paths,['obs_primary_mode','mod_primary_mode'],'primary_mode')
# access distance
temp_df = melt_df(compare_paths,['obs_acc_dist','mod_acc_dist'],'acc_dist')
compare_paths_melt = compare_paths_melt.merge(temp_df, how='left')
# egress distance
temp_df = melt_df(compare_paths,['obs_egr_dist','mod_egr_dist'],'egr_dist')
compare_paths_melt = compare_paths_melt.merge(temp_df, how='left')
# egress time
temp_df = melt_df(compare_paths,['obs_egr_time','mod_egr_time'],'egr_time')
compare_paths_melt = compare_paths_melt.merge(temp_df, how='left')
# access time
temp_df = melt_df(compare_paths,['obs_acc_time','mod_acc_time'],'acc_time')
compare_paths_melt = compare_paths_melt.merge(temp_df, how='left')
# xfer distance
temp_df = melt_df(compare_paths,['obs_xfer_dist','mod_xfer_dist'],'xfer_dist')
compare_paths_melt = compare_paths_melt.merge(temp_df, how='left')
# xfer distance
temp_df = melt_df(compare_paths,['obs_xfer_time','mod_xfer_time'],'xfer_time')
compare_paths_melt = compare_paths_melt.merge(temp_df, how='left')
# xfer count
temp_df = melt_df(compare_paths,['obs_xfer_count','mod_xfer_count'],'xfer_count')
compare_paths_melt = compare_paths_melt.merge(temp_df, how='left')

outfile_melt = os.path.join(OUT_DIR, 'pathset_compare_melt.csv')
compare_paths_melt.to_csv(outfile_melt, index=False)

print "Finished preparation in %5.2f mins" % ((time.time() - start)/60.0)
    
    

