######################################################################################################
# Converts OBS to dyno-path format (https://github.com/osplanning-data-standards/dyno-path)
# Reads: OBSdata_wBART_wSFtaz_wStops.csv, trip_list.txt (for person_trip_id)
# Writes: OBS_FToutput_links.csv
#######################################################################################################
import pandas as pd
import sys

pd.set_option('display.width', 300)

AccEgrs_dict = {'bike':'bike', 'pnr':'PNR', 'knr':'KNR', '.':'walk'}

# stop ids are strings, not floats
df = pd.read_csv('OBSdata_wBART_wSFtaz_wStops.csv',
                 dtype={"survey_board_stop_id"       :object,
                        "survey_board_stop_sequence" :object, # treat as string
                        "survey_alight_stop_id"      :object,
                        "survey_alight_stop_sequence":object, # treat as string
                        "first_board_stop_id"        :object,
                        "last_alight_stop_id"        :object,
                        "trip_id"                    :object},
                 na_values=["None"])

trip_list_df = pd.read_csv('trip_list.txt',sep=',',
                           dtype={"person_trip_id":object})

# assume walk for missing access/egress mode
df['access_mode'].fillna('walk', inplace=True)
df['egress_mode'].fillna('egress', inplace=True)
df['access_mode'] = df['access_mode'].replace(AccEgrs_dict)
df['egress_mode'] = df['egress_mode'].replace(AccEgrs_dict)

print 'Preparation'
print "  Have %6d rows" % len(df)

print "Removing 3-leg trips where either first or last leg was surveyed",
df["remove"] = False
df.loc[ (df["boardings"]==3)&(pd.isnull(df["transfer_from"])|pd.isnull(df["transfer_to"])), "remove"] = True
print " => dropping %d" % df["remove"].sum()
df = df.loc[df["remove"] == False]
print "  Have %6d rows" % len(df)

print "Removing trips with more than 3 boardings",
df.loc[ df["boardings"] > 3, "remove"] = True
print " => dropping %d" % df["remove"].sum()
df = df.loc[df["remove"] == False]
print "  Have %6d rows" % len(df)

print "Removing trips with two boarding and unknown transfer",
df.loc[ (df["boardings"]==2)&pd.isnull(df["transfer_from"])&pd.isnull(df["transfer_to"]), "remove"] = True
print " => dropping %d" % df["remove"].sum()
df = df.loc[df["remove"] == False]
print "  Have %6d rows" % len(df)

# get person_trip_id,time_target, and mode from trip_list
df = pd.merge(left     =df,
              right    =trip_list_df[["person_id","person_trip_id","time_target","mode"]],
              left_on  ="Unique_ID",
              right_on ="person_id",
              how      ="left",
              indicator=True)

print "Removing trips not in trip_list.txt",
df.loc[ df["_merge"]=="left_only", "remove"] = True
print " => dropping %d" % df["remove"].sum()
df = df.loc[df["remove"] == False]
print "  Have %6d rows" % len(df)

# add dyno-path columns
df["pathdir"] = 1  # outbound (time_target=arrival)
df.loc[df["time_target"]=="departure", "pathdir"] = 2 # inbound (time_target=departure)
df.rename(columns={"mode":"pathmode"}, inplace=True)

print 'Converting to links'

# access -- everyone has this
access_df    = df.copy()
access_df["linkmode"  ] = "access"
access_df["A_id"      ] = access_df["orig_sf_taz"]
access_df["A_seq"     ] = ""
access_df["B_id"      ] = access_df["first_board_stop_id"]
access_df["B_seq"     ] = ""
access_df["mode"      ] = access_df["access_mode"] + "_access"
access_df["route_id"  ] = ""
access_df["trip_id"   ] = ""
access_df["service_id"] = ""
access_df["agency_id" ] = ""
access_df["linknum"   ] = 0

# previous leg -- only if boardings > 1 and transfer_from
transit_prev_df  = df.loc[ (df["boardings"]>1)&pd.notnull(df["transfer_from"]) ].copy()
transit_prev_df["linkmode"  ] = "transit"
transit_prev_df["A_id"      ] = transit_prev_df["first_board_stop_id"]
transit_prev_df["A_seq"     ] = ""
transit_prev_df["B_id"      ] = "" # don't know
transit_prev_df["B_seq"     ] = ""
transit_prev_df["mode"      ] = transit_prev_df["first_board_mode"]
transit_prev_df["route_id"  ] = "" # don't know
transit_prev_df["trip_id"   ] = ""
transit_prev_df["agency_id" ] = transit_prev_df["agency_id transfer_from"]
transit_prev_df["service_id"] = transit_prev_df["service_id transfer_from"]
transit_prev_df["linknum"   ] = 1

transfer_prev_df = df.loc[ (df["boardings"]>1)&pd.notnull(df["transfer_from"]) ].copy()
transfer_prev_df["linkmode"  ] = "transfer"
transfer_prev_df["A_id"      ] = "" # don't know
transfer_prev_df["A_seq"     ] = ""
transfer_prev_df["B_id"      ] = transfer_prev_df["survey_board_stop_id" ]
transfer_prev_df["B_seq"     ] = ""
transfer_prev_df["mode"      ] = "transfer"
transfer_prev_df["route_id"  ] = "" # none
transfer_prev_df["trip_id"   ] = "" # none
transfer_prev_df["agency_id" ] = "" # none
transfer_prev_df["service_id"] = "" # none
transfer_prev_df["linknum"   ] = 2

# survey transit leg -- everyone has this
transit_df  = df.copy()
transit_df["linkmode"] = "transit"
transit_df["A_id"    ] = transit_df["survey_board_stop_id" ]
transit_df["A_seq"   ] = transit_df["survey_board_stop_sequence"]
transit_df["B_id"    ] = transit_df["survey_alight_stop_id"]
transit_df["B_seq"   ] = transit_df["survey_alight_stop_sequence"]
transit_df["mode"    ] = transit_df["survey_mode"]
# transit_df["route_id"  ] set already
# transit_df["trip_id"   ] set already
# transit_df["agency_id" ] set already
# transit_df["service_id"] set already
# if the trip_id is null though, route_id isn't useful
transit_df.loc[pd.isnull(transit_df["trip_id"]), "route_id"] = None
transit_df["linknum" ] = -1
transit_df.loc[ transit_df["boardings"]==1, "linknum"] = 1
transit_df.loc[(transit_df["boardings"]==2)&pd.notnull(transit_df["transfer_to"  ]), "linknum"] = 1
transit_df.loc[(transit_df["boardings"] >1)&pd.notnull(transit_df["transfer_from"]), "linknum"] = 3

# next leg -- only if boardings > 1 and transfer_to
transfer_next_df = df.loc[ (df["boardings"]>1)&pd.notnull(df["transfer_to"]) ].copy()
transfer_next_df["linkmode"  ] = "transfer"
transfer_next_df["A_id"      ] = transfer_next_df["survey_alight_stop_id"]
transfer_next_df["A_seq"     ] = ""
transfer_next_df["B_id"      ] = "" # don't know
transfer_next_df["B_seq"     ] = ""
transfer_next_df["mode"      ] = "transfer"
transfer_next_df["route_id"  ] = "" # none
transfer_next_df["trip_id"   ] = "" # none
transfer_next_df["agency_id" ] = "" # none
transfer_next_df["service_id"] = "" # none
transfer_next_df["linknum"   ] = transfer_next_df["boardings"]*2-2

# next leg -- only if boardings > 1 and transfer_to
transit_next_df  = df.loc[ (df["boardings"]>1)&pd.notnull(df["transfer_to"]) ].copy()
transit_next_df["linkmode"  ] = "transit"
transit_next_df["A_id"      ] = "" # don't know
transit_next_df["A_seq"     ] = ""
transit_next_df["B_id"      ] = transit_next_df["last_alight_stop_id"]
transit_next_df["B_seq"     ] = ""
transit_next_df["mode"      ] = transit_next_df["last_alight_mode"]
transit_next_df["route_id"  ] = "" # don't know
transit_next_df["trip_id"   ] = "" # don't know
transit_next_df["agency_id" ] = transit_next_df["agency_id transfer_to"]
transit_next_df["service_id"] = transit_next_df["service_id transfer_to"]
transit_next_df["linknum"   ] = transit_next_df["boardings"]*2-1

# egress -- everyone has this
egress_df    = df.copy()
egress_df["linkmode"  ] = "egress"
egress_df["A_id"      ] = egress_df["last_alight_stop_id"]
egress_df["A_seq"     ] = ""
egress_df["B_id"      ] = egress_df["dest_sf_taz"]
egress_df["B_seq"     ] = ""
egress_df["mode"      ] = egress_df["egress_mode"] + "_egress"
egress_df["route_id"  ] = ""
egress_df["trip_id"   ] = ""
egress_df["agency_id" ] = ""
egress_df["service_id"] = ""
egress_df["linknum"   ] = egress_df["boardings"]*2

# put them all together
path_links_df = pd.concat([access_df, transit_prev_df, transfer_prev_df, transit_df, transfer_next_df, transit_next_df, egress_df], axis=0)

# keep only the columns we want and output links
path_links_df = path_links_df[['person_id','person_trip_id','linkmode','A_id','A_seq','B_id','B_seq','linknum','mode','route_id','trip_id','agency_id','service_id']]
path_links_df.sort_values(by=["person_id","person_trip_id","linknum"], inplace=True)

# write it
path_links_df.to_csv('OBS_FToutput_links.csv',index=False)
print "Wrote OBS_FToutput_links.csv"

# keep only the columns we want and output paths
df = df[['person_id','person_trip_id','pathdir','pathmode']]
df.sort_values(by=["person_id","person_trip_id"], inplace=True)
df.to_csv('OBS_FToutput_paths.csv',index=False)
print "Wrote OBS_FToutput_paths.csv"
