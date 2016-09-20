######################################################################################################
# Converts OBS to FT passengers links output
# Reads: OBSdata_wBART_wSFtaz_wStops.csv
# Writes: OBS_FToutput.csv
#######################################################################################################
import pandas as pd

AccEgrs_dict = {'bike':'bike', 'pnr':'PNR', 'knr':'KNR', '.':'walk'}
transit_dict = {'commuter rail':'commuter_rail', 'express bus':'express_bus', 'local bus':'local_bus', 
                'heavy rail':'heavy_rail', 'light rail':'light_rail','ferry':'ferry', 'NA':'transit'}
agency_dict = {
	"AC Transit"					:"ac_transit",
	"AC TRANSIT"					:"ac_transit",
	"ACE"							:"ace",
	"AMTRAK"						:"amtrak",
	"BART"							:"bart",
	"Caltrain"						:"caltrain",
	"CALTRAIN"						:"caltrain",
	"County Connection"				:"cccta",
	"COUNTY CONNECTION"				:"cccta",
	"Golden Gate Transit (bus)"		:"golden_gate_transit",
	"Golden Gate Transit (ferry)"	:"ferry",
	"GOLDEN GATE FERRY"				:"ferry",
	"GOLDEN GATE TRANSIT"			:"golden_gate_transit",
	"MUNI"							:"sf_muni",
	"Napa Vine"						:"vine",
	"NAPA VINE"						:"vine",
	"Petaluma"						:"petaluma",
	"PETALUMA TRANSIT"				:"petaluma",
	"SamTrans"						:"samtrans",
	"SAMTRANS"						:"samtrans",
	"SANTA ROSA CITY BUS"			:"santa_rosa",
	"SANTA ROSA CITYBUS"			:"santa_rosa",
	"Santa Rosa CityBus"			:"santa_rosa",
	"BLUE & GOLD FERRY"				:"ferry",
	"SF Bay Ferry"					:"ferry",
	"SF BAY FERRY"					:"ferry",
	"SOLTRANS"						:"soltrans",
	"Sonoma County"					:"sonoma_county_transit",
	"SONOMA COUNTY TRANSIT"			:"sonoma_county_transit",
	"Tri-Delta"						:"tri_delta_transit",
	"TRI-DELTA"						:"tri_delta_transit",
	"Union City"					:"union_city_transit",
	"UNION CITY"					:"union_city_transit",
	"LAVTA"							:"lavta",
	"VTA"							:"scvta",
	"WESTCAT"						:"westcat",
	"WHEELS (LAVTA)"				:"lavta",
	"DUMBARTON EXPRESS"				:"UNMODELED",
	"EMERY-GO-ROUND"				:"UNMODELED",
	"FAIRFIELD-SUISUN"				:"UNMODELED",
	"STANFORD SHUTTLES"				:"UNMODELED",
	"VALLEJO TRANSIT"				:"UNMODELED",
	"MARIN TRANSIT"					:"UNMODELED",
	"PRIVATE SHUTTLE"				:"UNMODELED",
	"OTHER"							:"UNMODELED",
	"MODESTO TRANSIT"				:"EXTERNAL",
	"RIO-VISTA"						:"EXTERNAL",
	"SAN JOAQUIN TRANSIT"			:"EXTERNAL"
	}

Output = pd.DataFrame()
cols = ['person_id','trip_list_id_num','linkmode','A_id_num','B_id_num','linknum','mode','route_id','agency']

df = pd.read_csv('OBSdata_wBART_wSFtaz_wStops.csv')

# assume walk for missing access/egress mode
df['access_mode'].fillna('walk', inplace=True)
df['egress_mode'].fillna('egress', inplace=True)
df['access_mode'] = df['access_mode'].replace(AccEgrs_dict)
df['egress_mode'] = df['egress_mode'].replace(AccEgrs_dict)

print 'Preparation'
#Removing 3-leg trips where either first or last leg was surveyed
for i in range(len(df)):
    if (df.loc[i,'boardings']==3):
        if (df.loc[i,'transfer_from']=='None') or (df.loc[i,'transfer_to']=='None'):
            df2 = df.drop([i])
            df = df2

df = df[df.boardings <= 3]  #Removes trips with more than 2 transfers 
df = df.reset_index(drop=True)

print 'Main'
k=0   #link_num indicator
for i in range(len(df)):
    print i
    per_id = df.loc[i,'Unique_ID']
    trip_list_id_num = i+1
    
    #Access
    mode = df.loc[i,'access_mode'] + '_access'
    A_id = df.loc[i,'orig_sf_taz']     #For access links, A_id is a taz     
    B_id = df.loc[i,'first_board_stop_id']
    acc_strn = [(per_id, trip_list_id_num, 'access', A_id, B_id, 0, mode, '', '')]
    Output = Output.append(acc_strn)
 
    #No transfer
    if (df.loc[i,'boardings']==1):
        mode = transit_dict[df.loc[i,'survey_tech']]
		agency = agency_dict[df.loc[i,'operator']]
        route_id = df.loc[i,'route_id']
        A_id = df.loc[i,'first_board_stop_id']
        B_id = df.loc[i,'last_alight_stop_id']
        trn_strn = [(per_id, trip_list_id_num, 'transit', A_id, B_id, 1, mode, route_id, agency)]
        Output = Output.append(trn_strn)
        k=1
             
    #One transfer
    elif (df.loc[i,'boardings']==2):
        if (df.loc[i,'transfer_from']=='None'):  #first leg being surveyed
            mode = transit_dict[df.loc[i,'first_board_tech']]
			agency = agency_dict[df.loc[i,'operator']]
            route_id = df.loc[i,'route_id']
            A_id = df.loc[i,'first_board_stop_id']
            B_id = df.loc[i,'survey_alight_stop_id']
            trn_strn = [(per_id, trip_list_id_num, 'transit', A_id, B_id, 1, mode, route_id, agency)]
            Output = Output.append(trn_strn)
        
            A_id = df.loc[i,'survey_alight_stop_id']
            B_id = ''
            xfer_strn = [(per_id, trip_list_id_num, 'transfer', A_id, B_id, 2, 'transfer', '', '')]
            Output = Output.append(xfer_strn)
        
            mode = transit_dict[df.loc[i,'last_alight_tech']]
            agency = agency_dict[df.loc[i,'transfer_to']]
            A_id = ''  
            B_id = df.loc[i,'last_alight_stop_id']
            trn_strn = [(per_id, trip_list_id_num, 'transit', A_id, B_id, 3, mode, '', agency)]
            Output = Output.append(trn_strn)
            k=3
        
        else:  #last leg being surveyed
        #elif (df.loc[i,'transfer_to']=='None'):  
            mode = transit_dict[df.loc[i,'first_board_tech']]
            agency = agency_dict[df.loc[i,'transfer_from']]
            A_id = df.loc[i,'first_board_stop_id']
            B_id = ''  
            trn_strn = [(per_id, trip_list_id_num, 'transit', A_id, B_id, 1, mode, '', agency)]
            Output = Output.append(trn_strn)
        
            A_id = ''  
            B_id = df.loc[i,'survey_board_stop_id']
            xfer_strn = [(per_id, trip_list_id_num, 'transfer', A_id, B_id, 2, 'transfer', '', '')]
            Output = Output.append(xfer_strn)
        
            mode = transit_dict[df.loc[i,'last_alight_tech']]
            agency = agency_dict[df.loc[i,'operator']]
			route_id = df.loc[i,'route_id']
            A_id = df.loc[i,'survey_board_stop_id']
            B_id = df.loc[i,'last_alight_stop_id']
            trn_strn = [(per_id, trip_list_id_num, 'transit', A_id, B_id, 3, mode, route_is, agency)]
            Output = Output.append(trn_strn)
            k=3
                        
    #Two transfers
    else:  #3-leg trips (with 2 transfers) where the 2nd leg was surveyed
        mode = transit_dict[df.loc[i,'first_board_tech']]
        agency = agency_dict[df.loc[i,'transfer_from']]
        A_id = df.loc[i,'first_board_stop_id']
        B_id = ''  
        trn_strn = [(per_id, trip_list_id_num, 'transit', A_id, B_id, 1, mode, '', agency)]
        Output = Output.append(trn_strn)
        
        A_id = ''  
        B_id = df.loc[i,'survey_board_stop_id']
        xfer_strn = [(per_id, trip_list_id_num, 'transfer', A_id, B_id, 2, 'transfer', '', '')]
        Output = Output.append(xfer_strn)
        
        mode = transit_dict[df.loc[i,'survey_tech']]
        agency = agency_dict[df.loc[i,'operator']]
		route_id = df.loc[i,'route_id']
        A_id = df.loc[i,'survey_board_stop_id']
        B_id = df.loc[i,'survey_alight_stop_id']  
        trn_strn = [(per_id, trip_list_id_num, 'transit', A_id, B_id, 3, mode, route_id, agency)]
        Output = Output.append(trn_strn)
        
        A_id = df.loc[i,'survey_alight_stop_id']    
        B_id = ''
        xfer_strn = [(per_id, trip_list_id_num, 'transfer', A_id, B_id, 4, 'transfer', '', '')]
        Output = Output.append(xfer_strn)
        
        mode = transit_dict[df.loc[i,'last_alight_tech']]
        agency = agency_dict[df.loc[i,'transfer_to']]
        A_id = ''
        B_id = df.loc[i,'last_alight_stop_id']  #For egress links, B_id is a taz
        trn_strn = [(per_id, trip_list_id_num, 'transit', A_id, B_id, 5, mode, '', agency)]
        Output = Output.append(trn_strn)
        k=5
        
    #Egress
    mode = df.loc[i,'egress_mode'] + '_egress'
    A_id = df.loc[i,'last_alight_stop_id']
    B_id = df.loc[i,'dest_sf_taz']
    egr_strn = [(per_id, trip_list_id_num, 'egress', A_id, B_id, str(k+1), mode, '', '')]
    Output = Output.append(egr_strn)
    
Output.columns = cols
Output.to_csv('OBS_FToutput.csv',index=False)

print "Done!"