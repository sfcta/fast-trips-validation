### Various utility functions
import pandas as pd
from math import radians, cos, sin, asin, sqrt

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

def time_period(t):
    if type(t) == str:
        t = t.split(':')
        t = float(t[0]) + float(t[1])/60
    if t >= 3 and t < 6: return 'EA'
    elif t >= 6 and t < 9: return 'AM'
    elif t >= 9 and t < 15.5: return 'MD'
    elif t >= 15.5 and t < 18.5: return 'PM'
    elif t >= 18.5 or t < 3: return 'EV'
    else: return None

def prim_mode_hierarchy(df_pths, df_lnks, pri_mode_var):
    MODE_HI = ['heavy_rail','ferry','commuter_rail','premium_bus','light_rail','express_bus','local_bus']
    missing_mode = '9 None'
    df_pths[pri_mode_var] = missing_mode
    i = 0
    for curr_mode in MODE_HI:
        temp_df = df_lnks[df_lnks['mode']==curr_mode]
        temp_df = temp_df.rename(columns={'mode':'tmp_mode'})
        temp_df = temp_df[['person_id','person_trip_id','tmp_mode']]
        temp_df = temp_df.drop_duplicates(['person_id','person_trip_id'])
        df_pths = df_pths.merge(temp_df, how='left')
        i += 1
        df_pths.loc[(df_pths[pri_mode_var]==missing_mode) & (df_pths['tmp_mode']==curr_mode), pri_mode_var] = str(i) + ' ' + curr_mode
        df_pths = df_pths.drop('tmp_mode', 1)
    return df_pths

#calculate access/egress distance
def get_dist(row, taz_coords, stop_coords):
    A_id = row[0]
    B_id = row[1]
    if A_id > 0 and B_id>0:
        A_lat = taz_coords.loc[A_id,'lat']
        A_lon = taz_coords.loc[A_id,'lon']
        B_lat = stop_coords.loc[B_id,'stop_lat']
        B_lon = stop_coords.loc[B_id,'stop_lon']
        return haversine(A_lon, A_lat, B_lon, B_lat)
    else: return 0        


