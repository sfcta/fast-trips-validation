######################################################################################################
# Converts OBS to FT passengers links output
# Reads: OBSdata_wBART_wSFtaz_wStops.csv
# Writes: OBS_FToutput_links.csv
#######################################################################################################
import pandas as pd
import sys

AccEgrs_dict = {'bike':'bike', 'pnr':'PNR', 'knr':'KNR', '.':'walk'}
transit_dict = {'commuter rail':'commuter_rail', 'express bus':'express_bus', 'local bus':'local_bus', 
                'heavy rail':'heavy_rail', 'light rail':'light_rail','ferry':'ferry', 'NA':'transit'}
agency_dict = {
    "AC Transit"                    :"ac_transit",
    "AC TRANSIT"                    :"ac_transit",
    "ACE"                           :"ace",
    "AMTRAK"                        :"amtrak",
    "BART"                          :"bart",
    "Caltrain"                      :"caltrain",
    "CALTRAIN"                      :"caltrain",
    "County Connection"             :"cccta",
    "COUNTY CONNECTION"             :"cccta",
    "Golden Gate Transit (bus)"     :"golden_gate_transit",
    "Golden Gate Transit (ferry)"   :"ferry",
    "GOLDEN GATE FERRY"             :"ferry",
    "GOLDEN GATE TRANSIT"           :"golden_gate_transit",
    "MUNI"                          :"sf_muni",
    "SF Muni Early Tranche"         :"sf_muni",
    "Napa Vine"                     :"vine",
    "NAPA VINE"                     :"vine",
    "Petaluma"                      :"petaluma",
    "PETALUMA TRANSIT"              :"petaluma",
    "SamTrans"                      :"samtrans",
    "SAMTRANS"                      :"samtrans",
    "SANTA ROSA CITY BUS"           :"santa_rosa",
    "SANTA ROSA CITYBUS"            :"santa_rosa",
    "Santa Rosa CityBus"            :"santa_rosa",
    "BLUE & GOLD FERRY"             :"ferry",
    "SF Bay Ferry"                  :"ferry",
    "SF BAY FERRY"                  :"ferry",
    "SOLTRANS"                      :"soltrans",
    "Sonoma County"                 :"sonoma_county_transit",
    "SONOMA COUNTY TRANSIT"         :"sonoma_county_transit",
    "Tri-Delta"                     :"tri_delta_transit",
    "TRI-DELTA"                     :"tri_delta_transit",
    "Union City"                    :"union_city_transit",
    "UNION CITY"                    :"union_city_transit",
    "LAVTA"                         :"lavta",
    "VTA"                           :"scvta",
    "WESTCAT"                       :"westcat",
    "WHEELS (LAVTA)"                :"lavta",
    "DUMBARTON EXPRESS"             :"UNMODELED",
    "EMERY-GO-ROUND"                :"UNMODELED",
    "FAIRFIELD-SUISUN"              :"UNMODELED",
    "STANFORD SHUTTLES"             :"UNMODELED",
    "VALLEJO TRANSIT"               :"UNMODELED",
    "MARIN TRANSIT"                 :"UNMODELED",
    "PRIVATE SHUTTLE"               :"UNMODELED",
    "OTHER"                         :"UNMODELED",
    "MODESTO TRANSIT"               :"EXTERNAL",
    "RIO-VISTA"                     :"EXTERNAL",
    "SAN JOAQUIN TRANSIT"           :"EXTERNAL"
    }

df = pd.read_csv('OBSdata_wBART_wSFtaz_wStops.csv')

# assume walk for missing access/egress mode
df['access_mode'].fillna('walk', inplace=True)
df['egress_mode'].fillna('egress', inplace=True)
df['access_mode'] = df['access_mode'].replace(AccEgrs_dict)
df['egress_mode'] = df['egress_mode'].replace(AccEgrs_dict)

print 'Preparation'
print "  Have %6d rows" % len(df)

print "Removing 3-leg trips where either first or last leg was surveyed"
df["remove"] = False
df.loc[ (df["boardings"]==3)&((df["transfer_from"]=="None")|(df["transfer_to"]=="None")), "remove"] = True
df = df.loc[df["remove"] == False]
print "  Have %6d rows" % len(df)

print "Removing trips with more than 3 boardings"
df.loc[ df["boardings"] > 3, "remove"] = True
df = df.loc[df["remove"] == False]
print "  Have %6d rows" % len(df)

print "Removing trips with two boarding and unknown transfer"
df.loc[ (df["boardings"]==2)&(df["transfer_from"]=="None")&(df["transfer_to"]=="None"), "remove"] = True
df = df.loc[df["remove"] == False]
print "  Have %6d rows" % len(df)


df = df.reset_index(drop=True)
df["trip_list_id_num"] = df.index+1

print 'Converting to links'

# access -- everyone has this
access_df    = df.copy()
access_df["linkmode"] = "access"
access_df["A_id"    ] = access_df["orig_sf_taz"]
access_df["B_id"    ] = access_df["first_board_stop_id"]
access_df["mode"    ] = access_df["access_mode"] + "_access"
access_df["route_id"] = ""
access_df["agency"  ] = ""
access_df["linknum" ] = 0

# previous leg -- only if boardings > 1 and transfer_from
transit_prev_df  = df.loc[ (df["boardings"]>1)&(df["transfer_from"]!="None") ].copy()
transit_prev_df["linkmode"] = "transit"
transit_prev_df["A_id"    ] = transit_prev_df["first_board_stop_id"]
transit_prev_df["B_id"    ] = "" # don't know
transit_prev_df["mode"    ] = transit_prev_df["first_board_tech"].replace(to_replace=transit_dict.keys(), value=transit_dict.values())
transit_prev_df["route_id"] = "" # don't know
transit_prev_df["agency"  ] = transit_prev_df["transfer_from"].replace(to_replace=agency_dict.keys(), value=agency_dict.values())
transit_prev_df["linknum" ] = 1

transfer_prev_df = df.loc[ (df["boardings"]>1)&(df["transfer_from"]!="None") ].copy()
transfer_prev_df["linkmode"] = "transfer"
transfer_prev_df["A_id"    ] = "" # don't know
transfer_prev_df["B_id"    ] = transfer_prev_df["survey_board_stop_id" ]
transfer_prev_df["mode"    ] = "transfer"
transfer_prev_df["route_id"] = "" # none
transfer_prev_df["agency"  ] = "" # none
transfer_prev_df["linknum" ] = 2

# survey transit leg -- everyone has this
transit_df  = df.copy()
transit_df["linkmode"] = "transit"
transit_df["A_id"    ] = transit_df["survey_board_stop_id" ]
transit_df["B_id"    ] = transit_df["survey_alight_stop_id"]
transit_df["mode"    ] = transit_df["survey_tech"].replace(to_replace=transit_dict.keys(), value=transit_dict.values())
transit_df["route_id"] = transit_df["route_id"]
transit_df["agency"  ] = transit_df["operator"].replace(to_replace=agency_dict.keys(), value=agency_dict.values())
transit_df["linknum" ] = -1
transit_df.loc[ transit_df["boardings"]==1, "linknum"] = 1
transit_df.loc[(transit_df["boardings"]==2)&(transit_df["transfer_to"  ]!="None"), "linknum"] = 1
transit_df.loc[(transit_df["boardings"] >1)&(transit_df["transfer_from"]!="None"), "linknum"] = 3

# next leg -- only if boardings > 1 and transfer_to
transfer_next_df = df.loc[ (df["boardings"]>1)&(df["transfer_to"]!="None") ].copy()
transfer_next_df["linkmode"] = "transfer"
transfer_next_df["A_id"    ] = transfer_next_df["survey_alight_stop_id"]
transfer_next_df["B_id"    ] = "" # don't know
transfer_next_df["mode"    ] = "transfer"
transfer_next_df["route_id"] = "" # none
transfer_next_df["agency"  ] = "" # none
transfer_next_df["linknum" ] = transfer_next_df["boardings"]*2-2

# next leg -- only if boardings > 1 and transfer_to
transit_next_df  = df.loc[ (df["boardings"]>1)&(df["transfer_to"]!="None") ].copy()
transit_next_df["linkmode"] = "transit"
transit_next_df["A_id"    ] = "" # don't know
transit_next_df["B_id"    ] = transit_next_df["last_alight_stop_id"]
transit_next_df["mode"    ] = transit_next_df["last_alight_tech"].replace(to_replace=transit_dict.keys(), value=transit_dict.values())
transit_next_df["route_id"] = "" # don't know
transit_next_df["agency"  ] = transit_next_df["transfer_to"].replace(to_replace=agency_dict.keys(), value=agency_dict.values())
transit_next_df["linknum" ] = transit_next_df["boardings"]*2-1

# egress -- everyone has this
egress_df    = df.copy()
egress_df["linkmode"] = "egress"
egress_df["A_id"    ] = egress_df["last_alight_stop_id"]
egress_df["B_id"    ] = egress_df["dest_sf_taz"]
egress_df["mode"    ] = egress_df["egress_mode"] + "_egress"
egress_df["route_id"] = ""
egress_df["agency"  ] = ""
egress_df["linknum" ] = egress_df["boardings"]*2

# put them all together
path_links_df = pd.concat([access_df, transit_prev_df, transfer_prev_df, transit_df, transfer_next_df, transit_next_df, egress_df], axis=0)
path_links_df.rename(columns={"Unique_ID":"person_id"}, inplace=True)

path_links_df.loc[ path_links_df["agency"] == "bart",     "route_id"] = "bart_unknown"
path_links_df.loc[ path_links_df["agency"] == "caltrain", "route_id"] = "caltrain_unknown"
path_links_df.loc[ path_links_df["agency"] == "sf_muni",  "route_id"] = "sf_muni_unknown"

# keep only the columns we want and output links
cols = ['person_id','trip_list_id_num','linkmode','A_id','B_id','linknum','mode','route_id','agency']
path_links_df = path_links_df[cols]
path_links_df.sort_values(by=["trip_list_id_num","linknum"], inplace=True)

# write it
path_links_df.to_csv('OBS_FToutput_links.csv',index=False)
print "Wrote OBS_FToutput_links.csv"