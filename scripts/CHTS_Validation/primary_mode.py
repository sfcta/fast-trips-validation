# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 15:09:41 2017

@author: jchang
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from math import radians, cos, sin, asin, sqrt
from sklearn.metrics import confusion_matrix
import seaborn as sn

mode_dict = {'heavy_rail':1,'commuter_rail':2,'premium_bus':3,'express_bus':6,'local_bus':7,'ferry':4,'light_rail':5, 'street_car':8, 'open_shuttle':9, 'transit':10, 'Null':11}    

link_ob = pd.read_csv(r'Q:/Data/Surveys/HouseholdSurveys/CHTS2012/Data/W1_CHTS_GPS_Final_Data_Deliverable_Wearable/pathset_links.csv')
path_ob = pd.read_csv(r'Q:/Data/Surveys/HouseholdSurveys/CHTS2012/Data/W1_CHTS_GPS_Final_Data_Deliverable_Wearable/pathset_paths.csv')
link_mo = pd.read_csv(r'Q:/Model Development/SHRP2-fasttrips/Task4/CHTS_fasttrips_demand_v0.4_stochastic_iter1_nocap/chosenpaths_links.csv')
path_mo = pd.read_csv(r'Q:/Model Development/SHRP2-fasttrips/Task4/CHTS_fasttrips_demand_v0.4_stochastic_iter1_nocap/chosenpaths_paths.csv')
link_mo_old = pd.read_csv(r'Q:/Model Development/SHRP2-fasttrips/Task4/CHTS_fasttrips_demand_v0.4_stochastic_iter1_nocap_old/chosenpaths_links.csv')
path_mo_old = pd.read_csv(r'Q:/Model Development/SHRP2-fasttrips/Task4/CHTS_fasttrips_demand_v0.4_stochastic_iter1_nocap_old/chosenpaths_paths.csv')

stops = pd.read_csv(r'Q:/Model Development/SHRP2-fasttrips/Task2/built_fasttrips_network_2012Base/draft1.11_fare/stops.txt')
TAZ = pd.read_csv(r'Q:/Model Development/SHRP2-fasttrips/Task2/built_fasttrips_network_2012Base/draft1.11_fare/taz_coords.txt')

## produce a dictionary: person id, person trip id, index of first link
def generate_trip_link_dict(path_df,link_df):
    path_df['index']=0
    for j in range(0,len(link_df.index)-1):
        if link_df.iloc[j]['person_id']!=link_df.iloc[j+1]['person_id'] or link_df.iloc[j]['person_trip_id']!=link_df.iloc[j+1]['person_trip_id']:
            pID = link_df.iloc[j+1]['person_id']
            ptID = link_df.iloc[j+1]['person_trip_id']
            row = path_df.index.get_indexer_for(path_df[(path_df['person_id'] == pID) & (path_df['person_trip_id'] == ptID)].index)
            if len(row)!=0:
                row_index = row[0]
                path_df.loc[row_index,'index'] = j+1           

def get_sec(time_str):
    if (pd.isnull(time_str))==False:
        h,m,s=time_str.split(':')
        return int(h)*3600+int(m)*60+int(s)
    else: return 0

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def get_dist(A_id,B_id):
    if A_id != 0 and B_id!=0:
        A_lat = stops[(stops['stop_id'])== A_id]['stop_lat'].values[0]
        A_lon = stops[(stops['stop_id'])== A_id]['stop_lon'].values[0]
        B_lat = stops[(stops['stop_id'])== B_id]['stop_lat'].values[0]
        B_lon = stops[(stops['stop_id'])== B_id]['stop_lon'].values[0]
        return haversine(A_lon, A_lat, B_lon, B_lat)
    else: return 0


def get_primary(links):
    modes = links['mode'].unique()
    modes=sorted(modes,key=mode_dict.get)
    return modes[0]
    

def compute_primary_mode(path_df, link_df):
    path_df['primary_mode_time'] = ''
    path_df['primary_mode_distance'] = ''
    for i in range(0,len(path_df)):      
        link_first=path_df.iloc[i]['index']
        if i == len(path_df)-1:
            link_last = len(link_df)
        else: link_last = path_df.iloc[i+1]['index']-1
        links = link_df.iloc[link_first:link_last, : ]
        
        links = links[links['linkmode']=='transit']
        #links = link_df[(link_df['person_id'] == pID) & (link_df['person_trip_id'] == ptID) & (link_df['linkmode'] == 'transit')]
        links['link_time'] = 0
        links['link_distance'] = 0
             
        for j in links.index.values:
            linktime = get_sec(links.loc[j]['alight_time'])-get_sec(links.loc[j]['board_time'])
            A_id = links.loc[j]['A_id']
            B_id = links.loc[j]['B_id']
            links.loc[j,'link_distance'] = get_dist(A_id,B_id)
            links.loc[j,'link_time'] = linktime
        
        if links['link_time'].all()== False:
            max_linktime=max(links['link_time'])
            primary_mode_t = links[(links['link_time']==max_linktime)]['mode'].values[0]
        else: primary_mode_t = get_primary(links)
        
        if links['link_distance'].all() == False:
            max_linkdist=max(links['link_distance'])
            primary_mode_d = links[(links['link_distance']==max_linkdist)]['mode'].values[0]
        else: primary_mode_d = get_primary(links)
        
        path_df.loc[i,'primary_mode_time']=primary_mode_t
        path_df.loc[i,'primary_mode_distance']=primary_mode_d
    
# (observed) for each person & person trip ID, return primary mode based on link time and distance
generate_trip_link_dict(path_ob,link_ob)
compute_primary_mode(path_ob,link_ob)
# (modeled) for each person & person trip ID, return primary mode based on link time
generate_trip_link_dict(path_mo,link_mo)
compute_primary_mode(path_mo,link_mo)

generate_trip_link_dict(path_mo_old,link_mo_old)
compute_primary_mode(path_mo_old,link_mo_old)

           
path_ob.to_csv('path_observed_with_primary_mode.csv')
path_mo.to_csv('path_modeled_with_primary_mode.csv')

# compare the primary modes and produce confusion matrix
# join primary mode columns based on person id and person trip id

pm_ob = path_ob[['person_id','person_trip_id','primary_mode_time','primary_mode_distance']]#.replace(np.nan,'Null',regex=True)
pm_mo = path_mo[['person_id','person_trip_id','primary_mode_time','primary_mode_distance']]#.replace(np.nan,'Null',regex=True)
pm_mo_old=path_mo_old[['person_id','person_trip_id','primary_mode_time','primary_mode_distance']]

pm_comp = pm_ob.merge(pm_mo,left_on=['person_id','person_trip_id'],right_on=['person_id','person_trip_id'],how='left').fillna('Null')

pm_comp_old = pm_ob.merge(pm_mo_old,left_on=['person_id','person_trip_id'],right_on=['person_id','person_trip_id'],how='left').fillna('Null')

cm_time = pd.crosstab(pm_comp['primary_mode_time_x'],pm_comp['primary_mode_time_y'],colnames=['Modeled'],rownames=['Observed'])
cm_distance = pd.crosstab(pm_comp['primary_mode_distance_x'],pm_comp['primary_mode_distance_y'],colnames=['Modeled'],rownames=['Observed'])

cm_time_old = pd.crosstab(pm_comp_old['primary_mode_time_x'],pm_comp_old['primary_mode_time_y'],colnames=['Modeled'],rownames=['Observed'])
cm_distance_old = pd.crosstab(pm_comp_old['primary_mode_distance_x'],pm_comp_old['primary_mode_distance_y'],colnames=['Modeled'],rownames=['Observed'])

cm_colnames = ['heavy_rail','commuter_rail','premium_bus','express_bus','local_bus','ferry','light_rail', 'street_car', 'open_shuttle', 'transit', 'Null']
#cm_colnames = sorted(list(mode_dict),key=mode_dict.get)

for i in range(0,len(cm_colnames)):
    if cm_colnames[i] not in cm_time.index:
        cm_time.loc[cm_colnames[i],:]=0
    if cm_colnames[i] not in cm_time.columns:
        cm_time.loc[:,cm_colnames[i]]=0
    if cm_colnames[i] not in cm_distance.index:
        cm_distance.loc[cm_colnames[i],:]=0
    if cm_colnames[i] not in cm_distance.columns:
        cm_distance.loc[:,cm_colnames[i]]=0                   
    if cm_colnames[i] not in cm_time_old.index:
        cm_time_old.loc[cm_colnames[i],:]=0
    if cm_colnames[i] not in cm_time_old.columns:
        cm_time_old.loc[:,cm_colnames[i]]=0
    if cm_colnames[i] not in cm_distance_old.index:
        cm_distance_old.loc[cm_colnames[i],:]=0
    if cm_colnames[i] not in cm_distance_old.columns:
        cm_distance_old.loc[:,cm_colnames[i]]=0                   

cm_time = cm_time[cm_colnames]
cm_time = cm_time.loc[cm_colnames,:].astype(int)

cm_distance= cm_distance[cm_colnames]
cm_distance = cm_distance.loc[cm_colnames,:].astype(int)

#cm_time_old = cm_time_old[cm_colnames]
#cm_time_old = cm_time_old.loc[cm_colnames,:].astype(int)
#
#cm_distance_old= cm_distance_old[cm_colnames]
#cm_distance_old = cm_distance_old.loc[cm_colnames,:].astype(int)

plt.figure()
ax = plt.axes()
sn.heatmap(cm_time, annot=True, fmt="d",ax=ax)
ax.set_title('Primary Mode (Time) Match between CHTS (Observed) and FastTrips (Modeled)')
plt.show()

#plt.figure()
#ax = plt.axes()
#sn.heatmap(cm_time_old, annot=True, fmt="d",ax=ax, annot_kws={"size":8})
#ax.set_title('Primary Mode (Time) Match between CHTS (Observed) and FastTrips Previous Version (Modeled)')
#plt.show()
#
##compare two versions
#cm_time_diff = cm_time-cm_time_old
#plt.figure()
#ax = plt.axes()
#sn.heatmap(cm_time_diff, annot=True, fmt="d",ax=ax, annot_kws={"size":8})
#ax.set_title('Primary Mode (Time) Match Improvement')
#plt.show()

#plt.figure()
#ax = plt.axes()
#sn.heatmap(cm_distance, annot=True, fmt="d",ax=ax)
#ax.set_title('Primary Mode (Distance) Match between CHTS (Observed) and FastTrips (Modeled)')
#plt.show()




