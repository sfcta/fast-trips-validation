###################################################################################
# Converts CHTS gps trips data to FT passenger links output.
# Reads: w_gpstrips.csv
# Writes: CHTS_FToutput.csv
##########################################################################################################
import pandas as pd
import numpy as np

transit = [11,15,16,17,19,20,22,23,24,25,26,27,29]
AccEgrs = [1,2,3,4,5,6,7,8,9,10]
transit_dict = {'11':'employer_shuttle', '15':'local_bus', '16':'premium_bus', '17':'heavy_rail', 
                '19':'open_shuttle', '20':'open_shuttle', '22':'local_bus', '23':'transit', '24':'heavy_rail', 
                '25':'inter_regional_rail', '26':'light_rail', '27':'street_car', '29':'ferry'}
AccEgrs_dict = {'1':'walk', '2':'bike', '3':'walk', '4':'walk', '5':'PNR', '6':'KNR', '7':'KNR',
                '8':'PNR', '9':'KNR', '10':'PNR'}
max_walk_time = 50  #access/egress walk
max_init_wait = 30
max_xfer_wait = 20  #may be increased if found that the location is not changed and for some reason the person has just been waiting in the stop.
max_egr_time = 2
				
Output = pd.DataFrame()
cols = ['person_id','trip_list_id_num','linkmode','A_id_num','B_id_num','date','new_A_time','new_B_time','new_linktime min','new_waittime min','board_time','alight_time','linknum','mode']

df = pd.read_csv('w_gpstrips.csv')

print 'Phase(a)'
#Converting hour-minute start/end time to minutes (time1 and time2)
time1 = []; time2 = []
for i in range(len(df)):
    h = int(df.loc[i,'start_time'].split(' ')[1].split(':')[0])
    m = int(df.loc[i,'start_time'].split(' ')[1].split(':')[1])
    time1.append(h*60 + m)
    h = int(df.loc[i,'end_time'].split(' ')[1].split(':')[0])
    m = int(df.loc[i,'end_time'].split(' ')[1].split(':')[1])
    time2.append(h*60 + m)
df.insert(7,'time1',time1)
df.insert(8,'time2',time2)

print 'Preparation'	
#Removing records where access/egress walk time > max_walk_time
for i in range(len(df)):
    if (df.loc[i,'travel_mode']==1) and (df.loc[i,'time2']-df.loc[i,'time1']>=max_walk_time):
        df2 = df.drop([i])
        df = df2
#Removing records where end_time < start_time 
df = df[df.time1 <= df.time2]
df = df.reset_index(drop=True)

#Sorting based on travel day trip id for each person
df_sorted = df.sort(['sampno','perno','gpstravdayid','gpstravdaytripid'])
df_sorted = df_sorted.reset_index(drop=True)
df = df_sorted

#Adding per_id column
per_id = []
for i in range(len(df)):
    per_id.append(str(df.loc[i,'sampno']) + '_' + str(df.loc[i,'perno'])+ '_' + str(df.loc[i,'gpstravdayid']))
df.insert(2,'per_id',per_id)

#Creating persons dataset
persons = []
for i in range(len(df)-1):
    if (df.loc[i,'per_id']!=df.loc[i+1,'per_id']):
        persons.append(df.loc[i,'per_id'])
persons.append(df.loc[len(df)-1,'per_id'])

#Get the number of records for each person
grp = df.groupby('per_id').count()   

print 'Main'
i=0
m=0
access = 0

for p in persons:
    print p
    while ((i < grp.loc[p,'sampno']+m) and (i<len(df))):
        print i
        if (df.loc[i,'travel_mode'] in transit):
            per_id = str(df.loc[i,'sampno']) + '_' + str(df.loc[i,'perno'])
            trip_id = df.loc[i,'gpstripid']
            date = df.loc[i,'start_time'].split(' ')[0]
        
            #Access
            if (i>0) and (df.loc[i-1,'travel_mode'] in AccEgrs) and (0 <= df.loc[i,'time1']-df.loc[i-1,'time2'] <= max_init_wait):
                access = 1
                mode = AccEgrs_dict[str(df.loc[i-1,'travel_mode'])] + '_access'
                A_id = 'redacted'
                B_id = 'redacted'
                A_time = df.loc[i-1,'start_time'].split(' ')[1] + ':00'
                B_time = df.loc[i-1,'end_time'].split(' ')[1] + ':00'
                linktime = df.loc[i-1,'time2']-df.loc[i-1,'time1']   #df.loc[i-1,'duration_min']
                acc_strn = [(per_id, trip_id, 'access', A_id, B_id, date, A_time, B_time, linktime, '', '', '', 0, mode)]
                Output = Output.append(acc_strn)
            else:
                #Generating a virtual access link
                B_time = df.loc[i,'start_time'].split(' ')[1] + ':00'
                acc_strn = [(per_id, trip_id, 'access', '', '', date, '', B_time, '', '', '', '', 0, '')]
                Output = Output.append(acc_strn)
        
            #Transit (first transit link)
            mode = transit_dict[str(df.loc[i,'travel_mode'])]
            A_id = 'redacted'
            B_id = 'redacted'
            if (i>0) and (access==1):
                A_time = df.loc[i-1,'end_time'].split(' ')[1] + ':00'
                wait = df.loc[i,'time1']-df.loc[i-1,'time2']   #df.loc[i-1,'gaptime']
                linktime = df.loc[i,'time2']-df.loc[i-1,'time2']
            else:
                A_time = df.loc[i,'start_time'].split(' ')[1] + ':00'
                wait = ''
                linktime = df.loc[i,'time2']-df.loc[i,'time1']   #df.loc[i,'duration_min']
            B_time = df.loc[i,'end_time'].split(' ')[1] + ':00'
            board_time = df.loc[i,'start_time'].split(' ')[1] + ':00'
            trn_strn = [(per_id, trip_id, 'transit', A_id, B_id, date, A_time, B_time, linktime, wait, board_time, B_time, 1, mode)]
            Output = Output.append(trn_strn)
            access = 0
        
            i=i+1
            k=2
            #Transfers 
            while (True):
                if (df.loc[i,'per_id']==p) and (df.loc[i,'travel_mode'] in transit) and (0 <= df.loc[i,'time1']-df.loc[i-1,'time2'] <= max_xfer_wait):
                
                    #Generating a virtual transfer link
                    linknum = k
                    k = k+1
                    xfer_strn = [(per_id, trip_id, 'transfer', '', '', date, '', '', '', '', '', '', linknum, 'transfer')]
                    Output = Output.append(xfer_strn)
                
                    #transit link
                    mode = transit_dict[str(df.loc[i,'travel_mode'])]
                    A_id = 'redacted'
                    B_id = 'redacted'
                    A_time = df.loc[i-1,'end_time'].split(' ')[1] + ':00'
                    B_time = df.loc[i,'end_time'].split(' ')[1] + ':00'
                    linktime = df.loc[i,'time2']-df.loc[i,'time1']   #df.loc[i,'duration_min']
                    wait = df.loc[i,'time1']-df.loc[i-1,'time2']
                    board_time = df.loc[i,'start_time'].split(' ')[1] + ':00'
                    linknum = k
                    k = k+1
                    trn_strn = [(per_id, trip_id, 'transit', A_id, B_id, date, A_time, B_time, linktime, wait, board_time, B_time, linknum, mode)]
                    Output = Output.append(trn_strn)
                    i=i+1
                
                elif (df.loc[i,'per_id']==p) and (df.loc[i+1,'per_id']==p) and (i<len(df)-1) and (df.loc[i,'travel_mode'] in AccEgrs) and (df.loc[i+1,'travel_mode'] in transit) and (0 <= df.loc[i+1,'time1']-df.loc[i,'time2'] <= max_xfer_wait):
                    #transfer link
                    A_id = 'redacted'
                    B_id = 'redacted'
                    A_time = df.loc[i,'start_time'].split(' ')[1] + ':00'
                    B_time = df.loc[i,'end_time'].split(' ')[1] + ':00'
                    linktime = df.loc[i,'time2']-df.loc[i,'time1']   #df.loc[i,'duration_min']
                    linknum = k
                    k = k+1
                    xfer_strn = [(per_id, trip_id, 'transfer', A_id, B_id, date, A_time, B_time, linktime, '', '', '', linknum, 'transfer')]
                    Output = Output.append(xfer_strn)
                    i=i+1
            
                    #transit link
                    mode = transit_dict[str(df.loc[i,'travel_mode'])]
                    A_id = 'redacted'
                    B_id = 'redacted'
                    A_time = df.loc[i-1,'end_time'].split(' ')[1] + ':00'
                    B_time = df.loc[i,'end_time'].split(' ')[1] + ':00'
                    linktime = df.loc[i,'time2']-df.loc[i-1,'time2']   #df.loc[i,'duration_min']
                    wait = df.loc[i,'time1']-df.loc[i-1,'time2']   #df.loc[i-1,'gaptime']
                    board_time = df.loc[i,'start_time'].split(' ')[1] + ':00'
                    linknum = k
                    k = k+1
                    trn_strn = [(per_id, trip_id, 'transit', A_id, B_id, date, A_time, B_time, linktime, wait, board_time, B_time, linknum, mode)]
                    Output = Output.append(trn_strn)
                    i=i+1
                
                else:
                    break
                          
            #Egress
            if i>=len(df):
                break
        
            if (df.loc[i,'per_id']==p) and (df.loc[i,'travel_mode'] in AccEgrs) and (0 <= df.loc[i,'time1']-df.loc[i-1,'time2'] <= max_egr_time):
                mode = AccEgrs_dict[str(df.loc[i,'travel_mode'])] + '_egress'
                A_id = 'redacted'
                B_id = 'redacted'
                A_time = df.loc[i,'start_time'].split(' ')[1] + ':00'
                B_time = df.loc[i,'end_time'].split(' ')[1] + ':00'
                linktime = df.loc[i,'time2']-df.loc[i,'time1']   #df.loc[i,'duration_min']
                linknum = k
                k = k+1
                egr_strn = [(per_id, trip_id, 'egress', A_id, B_id, date, A_time, B_time, linktime, '', '', '', linknum, mode)]
                Output = Output.append(egr_strn)
                i=i+1
            else:
                #Generating a virtual egress link
				A_time = df.loc[i-1,'end_time'].split(' ')[1] + ':00'
                linknum = k
                k = k+1
                egr_strn = [(per_id, trip_id, 'egress', '', '', date, A_time, '', '', '', '', '', linknum, '')]
                Output = Output.append(egr_strn)
   
        else:
            i=i+1
    m=i
    print 'm=',m
              
Output.columns = cols
Output.to_csv('CHTS_ft_output.csv',index=False)

print 'Done!'