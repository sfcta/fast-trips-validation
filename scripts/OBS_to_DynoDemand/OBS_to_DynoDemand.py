###################################################################################
# Converts on-board survey data to Dyno-Demand files
# Reads: OBSdata_wBART_wSFtaz.csv, DepartureTimeCDFs.dat
# Writes: household.txt, person.txt, trip_list.txt
##########################################################################################################
import pandas as pd
import os,sys
from util_functions import *

pd.set_option('display.width', 300)

Num_dict = {'zero':'0','one':'1', 'two':'2', 'three':'3', 'four':'4', 'five':'5', 
            'six':'6', 'seven':'7', 'eight':'8', 'nine':'9', 'ten':'10',
            'eleven':'11', 'twelve':'12', 'thirteen':'13', 'fourteen':'14', 'fifteen':'15',
            'four or more':'4', 'six or more':'6', 'ten or more':'10',
            'other':None}

Inc_dict = {'$10,000 to $25,000':'17500', '$25,000 to $35,000':'30000', '$35,000 to $50,000':'42500', 
            '$50,000 to $75,000':'62500', '$75,000 to $100,000':'87500', '$100,000 to $150,000':'125000', 
            '$35,000 or higher':'35000', 'under $35,000':'18000', 'under $10,000':'5000',
            '$150,000 or higher':'150000'}

work_status = ['full- or part-time', 'non-worker']
work_dict = {'full- or part-time':'full-time', 'non-worker':'unemployed'}

#Purposes are translated such that they align with those configured for pathweights
purp_dict = {'at work':'work', 'work':'work', 'work-related':'work_based', 'home':'work', 'college':'college', 
            'university':'college', 'school':'high_school', 'high school':'high_school', 'grade school':'grade_school', 
            'escorting':'grade_school', 'eat out':'other', 'shopping':'other', 'social recreation':'other', 
            'other maintenance':'other', 'other discretionary':'other'}

pass_media = ['Clipper','clipper','pass','exempt']

AccEgrs_dict = {'pnr':'PNR', 'knr':'KNR', '.':'walk'}

#############################################################################################################
dep_time_dist = readDistributionCDFs(os.path.join(os.path.dirname(os.path.realpath(__file__)), "DepartureTimeCDFs.dat"))

df = pd.read_csv('OBSdata_wBART_wSFtaz.csv',
                  dtype={"onoff_enter_station":object,
                         "onoff_exit_station" :object,
                         "persons"            :object,
                         "ID"                 :object,
                         "approximate_age"    :float,  # really should be int but there are missing values
                         "depart_hour"        :object},
                  na_values=["missing","Missing","refused"])
print "Read %d trips" % len(df)

#Removing unnecessary columns
df = df [['workers','vehicles','Unique_ID','ID','access_mode','depart_hour','egress_mode','fare_category','fare_medium','gender','household_income','persons','work_status','approximate_age','tour_purp','path_line_haul','dest_maz','dest_sf_taz','orig_maz','orig_sf_taz']]

# rename
df.rename(columns={"orig_sf_taz":"o_taz",
                   "dest_sf_taz":"d_taz"}, inplace=True)

#### Make hhveh strings with numbers ("2" instead of "two")
df["hh_vehicles"] = df["vehicles"].replace(Num_dict)

#### Pick midpoint for household income (keep as string)
df["hh_income"] = df["household_income"].replace(Inc_dict)
df["hh_income_float"] = pd.to_numeric(df["hh_income"])

#### Make persons strings with numbers
df["hh_size"] = df["persons"].replace(Num_dict)

#### Make workers strings with numbers
df["hh_workers"] = df["workers"].replace(Num_dict)

#### approximate age should be between [6,110] -- otherwise, invalidate
df["age"] = df["approximate_age"]
df.loc[(df["age"]<6)|(df["age"]>110), "age"] = None

#### remap work status
df["worker_status"] = df["work_status"].replace(work_dict)

#### set transit_pass=1 if the first word of fare_medium is in pass_media
df["fare_medium first_word"] = df["fare_medium"].str.split(" ").str.get(0)
# print df["fare_medium first_word"].value_counts()
df["transit_pass"] = 0
df.loc[ df["fare_medium first_word"].isin(pass_media), "transit_pass"] = 1

#### set disability based on fare_categ
df["disability"] = "none"
df.loc[df["fare_category"]=="disabled", "disability"] = "unknown disability"
# what about the "senior or disabled" fare_category?

#### remap purpose
df["purpose"] = df["tour_purp"].replace(purp_dict)

#### clean access and egress modes
# assume walk for missing
df["access_mode"].fillna("walk", inplace=True)
df["egress_mode"].fillna("egress", inplace=True)
# capitalize knr, pnr and call "." walk
df["access_mode"] = df["access_mode"].replace(AccEgrs_dict)
df["egress_mode"] = df["egress_mode"].replace(AccEgrs_dict)

#### create mode
df["mode"] = df["access_mode"] + "-transit-" + df["egress_mode"]

#### create departure time based on depart_hour
# create departure column = departure time in minutes after midnight
df["departure"]      = df["depart_hour"].map(lambda x: chooseTimeFromDistribution(dep_time_dist[x]), na_action='ignore')
df["departure_time"] = df["departure"].map(lambda x: convertTripTime(x), na_action='ignore')
df["arrival_time"]   = df["departure_time"]  # don't know
df["time_target"]    = "departure"           # don't know

#### Value of Time
'''VoT based on SFCTA RPM-9 Report, p39:
- non-work VoT = 2/3 work VoT,
- Impose a minimum of $1/hr and a maximum of $50/hr,
- Impose a maximum of $5/hr for workers younger than 18 years old.'''
df["vot"  ] = -1.0   # define it as an float type
df.loc[ (df["age"]<=18)&(df["worker_status"]=='full-time'),                 "vot"] = 5.0  # max $5 for workers under than 18 years old
df.loc[ pd.isnull(df["hh_income"])|(df["worker_status"]!='full-time'),      "vot"] = 1.0 # $1 for non-workers

# assume hh_workers=1 if not set or zero
df["hh_workers_float"] =  pd.to_numeric(df["hh_workers"])
df.loc[ (df["hh_workers"]=="0")|pd.isnull(df["hh_workers"]), "hh_workers_float"] = 1.0
# use it to set work vot
df["vot_w"] = (df["hh_income_float"]/df["hh_workers_float"]) / (52*40)

# if vot isn't set, set based on work vot and purpose
df.loc[ (df["vot"]<0)&(df["purpose"]=="work"), "vot" ] = df["vot_w"]
df.loc[ (df["vot"]<0)&(df["purpose"]!="work"), "vot" ] = 0.67*df["vot_w"]
# vot must be < 50
df.loc[ df["vot"] > 50.0, "vot"] = 50

# trips without origins or destinations are useless -- filter these out
df = df.loc[ pd.notnull(df["o_taz"]) ]
df = df.loc[ pd.notnull(df["d_taz"]) ]
# and make them ints
df["o_taz"] = df["o_taz"].astype(int)
df["d_taz"] = df["d_taz"].astype(int)
print "Filtered to %d trips" % len(df)

df["hh_id num"] = df.index + 1
df["hh_id"] = df["hh_id num"].map(lambda x: "hh%d" % x)
df["person_id"] = df["Unique_ID"]
df["person_trip_id"] = df.index + 1

# write out the relevant columns
household_df = df[['hh_id','hh_vehicles','hh_income','hh_size','hh_workers']]
household_df.to_csv("household.txt", index=False)

persons_df = df[['person_id','hh_id','age','gender','worker_status','transit_pass','disability']]
persons_df.to_csv("person.txt", index=False, float_format="%.0f")

trips_df = df[['person_id','person_trip_id','o_taz','d_taz','mode','purpose','departure_time','arrival_time','time_target','vot']]
trips_df.sort_values(by=["person_id"]).to_csv("trip_list.txt", index=False, float_format="%.2f")

print "Done!"