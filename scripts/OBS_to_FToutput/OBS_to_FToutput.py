######################################################################################################
# Converts OBS to FT passengers links output
# Reads: OBSdata_wBART_wSFtaz_wStops.csv
# Writes: OBS_FToutput.csv
#######################################################################################################
import pandas as pd

AccEgrs_dict = {'bike':'bike', 'walk':'walk', 'pnr':'PNR', 'knr':'KNR', 'NA':'walk', '.':'walk'}
transit_dict = {'commuter rail':'commuter_rail', 'express bus':'express_bus', 'local bus':'local_bus', 
                'heavy rail':'heavy_rail', 'light rail':'light_rail','ferry':'ferry', 'NA':'transit'}

Output = pd.DataFrame()
cols = ['person_id','trip_list_id_num','linkmode','A_id_num','B_id_num','linknum','mode','route_id']

df = pd.read_csv('OBSdata_wBART_wSFtaz_wStops.csv')

print 'Preparation'
#Removing 3-leg trips where either first or last leg was surveyed
for i in range(len(df)):
    if (df.loc[i,'boardings']==3):
        if (df.loc[i,'transfer_from']=='None') or (df.loc[i,'transfer_to']=='None'):
            df2 = df.drop([i])
            df = df2

df = df[df.boardings <= 3]  #Removes trips with more than 2 transfers 
df = df.reset_index(drop=True)
df = df.fillna(value='NA')

print 'Main'
k=0   #link_num indicator
for i in range(len(df)):
    print i
    per_id = 'hh' + str(i+1) + '_' + str(df.loc[i,'ID'])
    #per_id = df.loc[i,'person_id']
    trip_id = i+1
    
    #Access
    mode = AccEgrs_dict[df.loc[i,'access_mode']] + '_access'
    A_id = df.loc[i,'orig_sf_taz']     #For access links, A_id is a taz     
    B_id = df.loc[i,'first_board_stop']
    acc_strn = [(per_id, trip_id, 'access', A_id, B_id, 0, mode, '')]
    Output = Output.append(acc_strn)
 
    #No transfer
    if (df.loc[i,'boardings']==1):
        mode = transit_dict[str(df.loc[i,'survey_tech'])]
        route = df.loc[i,'operator'] + '_' + str(df.loc[i,'route'])
        A_id = df.loc[i,'first_board_stop']
        B_id = df.loc[i,'last_alight_stop']
        trn_strn = [(per_id, trip_id, 'transit', A_id, B_id, 1, mode, route)]
        Output = Output.append(trn_strn)
        k=1
             
    #One transfer
    elif (df.loc[i,'boardings']==2):
        if (df.loc[i,'transfer_from']=='None'):  #first leg being surveyed
            mode = transit_dict[str(df.loc[i,'first_board_tech'])]
            route = df.loc[i,'operator'] + '_' + str(df.loc[i,'route'])
            A_id = df.loc[i,'first_board_stop']
            B_id = df.loc[i,'survey_alight_stop']
            trn_strn = [(per_id, trip_id, 'transit', A_id, B_id, 1, mode, route)]
            Output = Output.append(trn_strn)
        
            A_id = df.loc[i,'survey_alight_stop']
            B_id = ''
            xfer_strn = [(per_id, trip_id, 'transfer', A_id, B_id, 2, 'transfer', '')]
            Output = Output.append(xfer_strn)
        
            mode = transit_dict[str(df.loc[i,'last_alight_tech'])]
            route = df.loc[i,'transfer_to']  #not a route, just agency
            A_id = ''  
            B_id = df.loc[i,'last_alight_stop']
            trn_strn = [(per_id, trip_id, 'transit', A_id, B_id, 3, mode, route)]
            Output = Output.append(trn_strn)
            k=3
        
        else:  #last leg being surveyed
        #elif (df.loc[i,'transfer_to']=='None'):  
            mode = transit_dict[str(df.loc[i,'first_board_tech'])]
            route = df.loc[i,'transfer_from']  #not a route, just agency
            A_id = df.loc[i,'first_board_stop']
            B_id = ''  
            trn_strn = [(per_id, trip_id, 'transit', A_id, B_id, 1, mode, route)]
            Output = Output.append(trn_strn)
        
            A_id = ''  
            B_id = df.loc[i,'survey_board_stop']
            xfer_strn = [(per_id, trip_id, 'transfer', A_id, B_id, 2, 'transfer', '')]
            Output = Output.append(xfer_strn)
        
            mode = transit_dict[str(df.loc[i,'last_alight_tech'])]
            route = df.loc[i,'operator'] + '_' + str(df.loc[i,'route'])
            A_id = df.loc[i,'survey_board_stop']
            B_id = df.loc[i,'last_alight_stop']
            trn_strn = [(per_id, trip_id, 'transit', A_id, B_id, 3, mode, route)]
            Output = Output.append(trn_strn)
            k=3
                        
    #Two transfers
    else:  #3-leg trips (with 2 transfers) where the 2nd leg was surveyed
        mode = transit_dict[str(df.loc[i,'first_board_tech'])]
        route = df.loc[i,'transfer_from']  #not a route, just agency
        A_id = df.loc[i,'first_board_stop']
        B_id = ''  
        trn_strn = [(per_id, trip_id, 'transit', A_id, B_id, 1, mode, route)]
        Output = Output.append(trn_strn)
        
        A_id = ''  
        B_id = df.loc[i,'survey_board_stop']
        xfer_strn = [(per_id, trip_id, 'transfer', A_id, B_id, 2, 'transfer', '')]
        Output = Output.append(xfer_strn)
        
        mode = transit_dict[str(df.loc[i,'survey_tech'])]
        route = df.loc[i,'operator'] + '_' + str(df.loc[i,'route']) 
        A_id = df.loc[i,'survey_board_stop']
        B_id = df.loc[i,'survey_alight_stop']  
        trn_strn = [(per_id, trip_id, 'transit', A_id, B_id, 3, mode, route)]
        Output = Output.append(trn_strn)
        
        A_id = df.loc[i,'survey_alight_stop']    
        B_id = ''
        xfer_strn = [(per_id, trip_id, 'transfer', A_id, B_id, 4, 'transfer', '')]
        Output = Output.append(xfer_strn)
        
        mode = transit_dict[str(df.loc[i,'last_alight_tech'])]
        route = df.loc[i,'transfer_to']  #not a route, just agency
        A_id = ''
        B_id = df.loc[i,'last_alight_stop']  #For egress links, B_id is a taz
        trn_strn = [(per_id, trip_id, 'transit', A_id, B_id, 5, mode, route)]
        Output = Output.append(trn_strn)
        k=5
        
    #Egress
    mode = AccEgrs_dict[df.loc[i,'egress_mode']] + '_egress'
    A_id = df.loc[i,'last_alight_stop']
    B_id = df.loc[i,'dest_sf_taz']
    egr_strn = [(per_id, trip_id, 'egress', A_id, B_id, str(k+1), mode, '')]
    Output = Output.append(egr_strn)
    
df = df.fillna(value='')
Output.columns = cols
Output.to_csv('OBS_FToutput.csv',index=False)

print "Done!"