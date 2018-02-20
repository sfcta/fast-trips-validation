###################################################################################
# Converts CHTS gps trips data to FT passenger links output. This script attempts to
# identify all transit path details about access, egress, and transfer points from 
# GPS point data. The output is an intermediate file that requires further processing 
# to transform it to dyno-path format.
# Reads: w_gpstrips.csv
# Writes: CHTS_FToutput.csv
####################################################################################
import pandas as pd

# Do not include paratransit (21)
AccEgrs = [1,2,3,4,5,6,7,8,9,10]
AccEgrs_dict = {'1':'walk', '2':'bike', '3':'walk', '4':'walk', '5':'PNR', '6':'KNR', '7':'KNR',
                '8':'PNR', '9':'KNR', '10':'PNR'}
#Do not include: private transit/shuttles (11,14), Greyhound (12), Plane(13), LA metro lines (17), School bus (18), Amtrak bus(22)
transit = [15,16,19,20,23,24,25,26,27,29]
transit_dict = {'15':'local_bus', '16':'premium_bus', '19':'open_shuttle', '20':'open_shuttle', 
                '23':'transit', '24':'heavy_rail', '25':'commuter_rail', '26':'light_rail', 
                '27':'street_car', '29':'ferry'}

MAX_WALK_TIME = 50  # Maximum assumed access/egress walk time in minutes for initial screening
MAX_INIT_WAIT = 30  # Maximum assumed initial wait time in minutes
MAX_XFER_WAIT = 21  # Maximum assumed xfer wait time. May be increased if found that the location is not changed and for some reason the person has just been waiting in the stop.
MAX_EGR_TIME = 10   # Maximum assumed egress time from transit stop/staton to final destination of trip
				
out_df = pd.DataFrame()
cols = ['person_id','trip_list_id_num','linkmode','A_lat','A_lon','B_lat','B_lon','travel_date','new_A_time','new_B_time','new_linktime_min','new_waittime_min','board_time','alight_time','linknum','mode','transit_mode_no']
df = pd.read_csv('w_gpstrips.csv')

#################################### Preparation ####################################
print 'Preparation'	
#Create travel_date
df['travel_date'] = pd.to_datetime(df['start_time'].str.split(' ').str.get(0)).dt.date
df['end_seg_date'] = pd.to_datetime(df['end_time'].str.split(' ').str.get(0)).dt.date
df['start'] = df['start_time'].str.split(' ').str.get(1)
df['end'] = df['end_time'].str.split(' ').str.get(1)
#Convert hour-minute start_time to minutes (time1)
df['time1'] = df['start'].str.split(':').str.get(0).astype(int)*60 + df['start'].str.split(':').str.get(1).astype(int)
#Convert hour-minute end_time to minutes (time2)
df['time2'] = df['end'].str.split(':').str.get(0).astype(int)*60 + df['end'].str.split(':').str.get(1).astype(int)
df.loc[(df['end_seg_date']-df['travel_date'])==pd.Timedelta('1 days'), 'time2'] = 1440 + df.loc[(df['end_seg_date']-df['travel_date'])==pd.Timedelta('1 days'), 'time2']

#Remove records where access/egress walk time > MAX_WALK_TIME
df = df.loc[~((df['travel_mode']==1) & (df['time2']-df['time1'] >= MAX_WALK_TIME)),]
#Remove records where end time(time2) < start time(time1) 
df = df.loc[df['time2']>=df['time1'],]
#Sort based on trip id for each travel day for each person in each household
df = df.sort_values(['sampno','perno','gpstravdayid','gpstravdaytripid']).reset_index(drop=True)

#Create person-trip dataset
df['prs_trp_id'] = df['sampno'].astype(str) + '_' + df['perno'].astype(str) + '_' + df['gpstravdayid'].astype(str)
PrsTrp = df[['prs_trp_id','sampno']].groupby('prs_trp_id').count().index
#Get the number of records for each person-day
grp = df[['prs_trp_id','sampno']].groupby('prs_trp_id').count() 

######## Build main body of the output file, except for route and stops id's ########
print 'Start building main body of output file'
i=0
m=0
access = 0

for p in PrsTrp:
    #print p
    while ((i < grp.loc[p,'sampno']+m) and (i<len(df))):
        #print i
        if (df.loc[i,'travel_mode'] in transit):
            per_id = str(df.loc[i,'sampno']) + '_' + str(df.loc[i,'perno'])
            trip_id = df.loc[i,'gpstripid']
            date = df.loc[i,'travel_date']
        
            #Access
            if (df.loc[i,'gpstravdaytripid']>0) and (df.loc[i-1,'travel_mode'] in AccEgrs) and (0 <= df.loc[i,'time1']-df.loc[i-1,'time2'] <= MAX_INIT_WAIT) and pd.notnull(df.loc[i,'distfromlastdest']):
                access = 1
                mode = AccEgrs_dict[str(df.loc[i-1,'travel_mode'])] + '_access'
                mode_no = '' #df.loc[i-1,'travel_mode']
                A_lat = df.loc[i-1,'origin_lat']
                A_lon = df.loc[i-1,'origin_lon']
                # TODO: Find A_id = origin_sftaz for A
                B_lat = df.loc[i-1,'destination_lat']
                B_lon = df.loc[i-1,'destination_lon']
                # TODO: Find B_id = destination_stop_id for B
                A_time = df.loc[i-1,'start'] + ':00'
                B_time = df.loc[i-1,'end'] + ':00'
                linktime = df.loc[i-1,'time2']-df.loc[i-1,'time1']   #df.loc[i-1,'duration_min']
                acc_strn = [(per_id, trip_id, 'access', A_lat, A_lon, B_lat, B_lon, date, A_time, B_time, linktime, '', '', '', 0, mode, mode_no)]
                out_df = out_df.append(acc_strn)
            else:
                #Generating a virtual access link
                temp_time = df.loc[i,'start'] + ':00'
                temp_lat = df.loc[i,'origin_lat']
                temp_lon = df.loc[i,'origin_lon']
                # Let us assume that the person is starting from the station itself instead of having an incomplete record
                acc_strn = [(per_id, trip_id, 'access', temp_lat, temp_lon, temp_lat, temp_lon, date, temp_time, temp_time, '', '', '', '', 0, 'walk_access', '')]
                out_df = out_df.append(acc_strn)
        
            #Transit (first transit link)
            mode = transit_dict[str(df.loc[i,'travel_mode'])]
            mode_no = df.loc[i,'travel_mode']
            A_lat = df.loc[i,'origin_lat']
            A_lon = df.loc[i,'origin_lon']
            # TODO: Find A_id = origin_stop_id for A
            B_lat = df.loc[i,'destination_lat']
            B_lon = df.loc[i,'destination_lon']
            # TODO: Find B_id = destination_stop_id for B
            if (df.loc[i,'gpstravdaytripid']>0) and (access==1):
                A_time = df.loc[i-1,'end'] + ':00'
                wait = df.loc[i,'time1']-df.loc[i-1,'time2']   #df.loc[i-1,'gaptime']
                linktime = df.loc[i,'time2']-df.loc[i-1,'time2']
            else:
                A_time = df.loc[i,'start'] + ':00'
                wait = ''
                linktime = df.loc[i,'time2']-df.loc[i,'time1']   #df.loc[i,'duration_min']
            B_time = df.loc[i,'end'] + ':00'
            board_time = df.loc[i,'start'] + ':00'
            trn_strn = [(per_id, trip_id, 'transit', A_lat, A_lon, B_lat, B_lon, date, A_time, B_time, linktime, wait, board_time, B_time, 1, mode, mode_no)]
            out_df = out_df.append(trn_strn)
            access = 0
        
            i=i+1
            k=2
            #Transfers 
            while (True):
                if (df.loc[i,'prs_trp_id']==p) and (df.loc[i,'travel_mode'] in transit) and (0 <= df.loc[i,'time1']-df.loc[i-1,'time2'] <= MAX_XFER_WAIT) and pd.notnull(df.loc[i,'distfromlastdest']):
                
                    #Generating a virtual transfer link
                    linknum = k
                    k = k+1
                    xfer_strn = [(per_id, trip_id, 'transfer', '', '', '', '', date, '', '', '', '', '', '', linknum, 'transfer','')]
                    out_df = out_df.append(xfer_strn)
                
                    #transit link
                    mode = transit_dict[str(df.loc[i,'travel_mode'])]
                    mode_no = df.loc[i,'travel_mode']
                    A_lat = df.loc[i,'origin_lat']
                    A_lon = df.loc[i,'origin_lon']
                    # TODO: Find A_id = origin_stop_id for A
                    B_lat = df.loc[i,'destination_lat']
                    B_lon = df.loc[i,'destination_lon']
                    # TODO: Find B_id = destination_stop_id for B
                    A_time = df.loc[i-1,'end'] + ':00'
                    B_time = df.loc[i,'end'] + ':00'
                    linktime = df.loc[i,'time2']-df.loc[i-1,'time2']   #df.loc[i,'duration_min']
                    wait = df.loc[i,'time1']-df.loc[i-1,'time2']
                    board_time = df.loc[i,'start'] + ':00'
                    linknum = k
                    k = k+1
                    trn_strn = [(per_id, trip_id, 'transit', A_lat, A_lon, B_lat, B_lon, date, A_time, B_time, linktime, wait, board_time, B_time, linknum, mode, mode_no)]
                    out_df = out_df.append(trn_strn)
                    i=i+1
                
                elif (df.loc[i,'prs_trp_id']==p) and (df.loc[i+1,'prs_trp_id']==p) and (i<len(df)-1) and (df.loc[i,'travel_mode'] in AccEgrs) and \
                (df.loc[i+1,'travel_mode'] in transit) and (0 <= df.loc[i+1,'time1']-df.loc[i,'time2'] <= MAX_XFER_WAIT) and pd.notnull(df.loc[i,'distfromlastdest']):
                    #transfer link
                    A_lat = df.loc[i,'origin_lat']
                    A_lon = df.loc[i,'origin_lon']
                    # TODO: Find A_id = origin_stop_id for A
                    B_lat = df.loc[i,'destination_lat']
                    B_lon = df.loc[i,'destination_lon']
                    # TODO: Find B_id = destination_stop_id for B
                    A_time = df.loc[i,'start'] + ':00'
                    B_time = df.loc[i,'end'] + ':00'
                    linktime = df.loc[i,'time2']-df.loc[i,'time1']   #df.loc[i,'duration_min']
                    linknum = k
                    k = k+1
                    xfer_strn = [(per_id, trip_id, 'transfer', A_lat, A_lon, B_lat, B_lon, date, A_time, B_time, linktime, '', '', '', linknum, 'transfer', '')]
                    out_df = out_df.append(xfer_strn)
                    i=i+1
            
                    #transit link
                    mode = transit_dict[str(df.loc[i,'travel_mode'])]
                    mode_no = df.loc[i,'travel_mode']
                    A_lat = df.loc[i,'origin_lat']
                    A_lon = df.loc[i,'origin_lon']
                    # TODO: Find A_id = origin_stop_id for A
                    B_lat = df.loc[i,'destination_lat']
                    B_lon = df.loc[i,'destination_lon']
                    # TODO: Find B_id = destination_stop_id for B
                    A_time = df.loc[i-1,'end'] + ':00'
                    B_time = df.loc[i,'end'] + ':00'
                    linktime = df.loc[i,'time2']-df.loc[i-1,'time2']   #df.loc[i,'duration_min']
                    wait = df.loc[i,'time1']-df.loc[i-1,'time2']   #df.loc[i-1,'gaptime']
                    board_time = df.loc[i,'start'] + ':00'
                    linknum = k
                    k = k+1
                    trn_strn = [(per_id, trip_id, 'transit', A_lat, A_lon, B_lat, B_lon, date, A_time, B_time, linktime, wait, board_time, B_time, linknum, mode, mode_no)]
                    out_df = out_df.append(trn_strn)
                    i=i+1
                
                else:
                    break
                          
            #Egress
            if i>=len(df):
                break
        
            if (df.loc[i,'prs_trp_id']==p) and (df.loc[i,'travel_mode'] in AccEgrs) and (0 <= df.loc[i,'time1']-df.loc[i-1,'time2'] <= MAX_EGR_TIME):
                mode = AccEgrs_dict[str(df.loc[i,'travel_mode'])] + '_egress'
                mode_no = '' #df.loc[i,'travel_mode']
                A_lat = df.loc[i,'origin_lat']
                A_lon = df.loc[i,'origin_lon']
                # TODO: Find A_id = origin_stop_id for A
                B_lat = df.loc[i,'destination_lat']
                B_lon = df.loc[i,'destination_lon']
                # TODO: Find B_id = destination_sftaz for B
                A_time = df.loc[i,'start'] + ':00'
                B_time = df.loc[i,'end'] + ':00'
                linktime = df.loc[i,'time2']-df.loc[i,'time1']   #df.loc[i,'duration_min']
                linknum = k
                k = k+1
                egr_strn = [(per_id, trip_id, 'egress', A_lat, A_lon, B_lat, B_lon, date, A_time, B_time, linktime, '', '', '', linknum, mode, mode_no)]
                out_df = out_df.append(egr_strn)
                i=i+1
            else:
                #Generating a virtual egress link
                temp_time = df.loc[i-1,'end'] + ':00'
                temp_lat = df.loc[i-1,'destination_lat']
                temp_lon = df.loc[i-1,'destination_lon']
                linknum = k
                k = k+1
                egr_strn = [(per_id, trip_id, 'egress', temp_lat, temp_lon, temp_lat, temp_lon, date, temp_time, temp_time, '', '', '', '', linknum, 'walk_egress', '')]
                out_df = out_df.append(egr_strn)
   
        else:
            i=i+1
    m=i
    #print 'm=',m
              
out_df.columns = cols
out_df.to_csv('CHTS_ft_output.csv',index=False)

print 'Done!'