###################################################################################
# Converts on-board survey data to Dyno-Demand files
# Reads: OBSdata_wBART_wSFtaz.csv, DepartureTimeCDFs.dat
# Writes: household.txt, person.txt, trip_list.txt
##########################################################################################################
import pandas as pd
import os,string,sys
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

#MTC defined time periods for survey
survey_time_period = {3 :'EARLY AM',
                      4 :'EARLY AM',
                      5 :'EARLY AM',
                      6 :'AM PEAK',
                      7 :'AM PEAK',
                      8 :'AM PEAK',
                      9 :'AM PEAK',
                      10:'MIDDAY',
                      11:'MIDDAY',
                      12:'MIDDAY',
                      13:'MIDDAY',
                      14:'MIDDAY',
                      15:'PM PEAK',
                      16:'PM PEAK',
                      17:'PM PEAK',
                      18:'PM PEAK',
                      19:'EVENING',
                      20:'EVENING',
                      21:'NIGHT',
                      22:'NIGHT',
                      23:'NIGHT',
                      0 :'NIGHT',
                      1 :'NIGHT',
                      2 :'NIGHT'}

hours = {'Before 6 a.m.'       : None,
         '6 - 6:59 a.m.'       : 6,
         '7 - 7:59 a.m.'       : 7,
         '8 - 8:59 a.m.'       : 8,
         '9 - 9:59 a.m.'       : 9,
        '10 - 10:59 a.m.'      : 10,
        '11 a.m. - 11:59 a.m.' : 11,
        '12 - 12:59 p.m.'      : 12,
        '1 - 1:59 p.m.'        : 13,
        '2 - 2:59 p.m.'        : 14,
        '3 - 3:59 p.m.'        : 15,
        '4 - 4:59 p.m.'        : 16,
        '5 - 5:59 p.m.'        : 17,
        '6 - 6:59 p.m.'        : 18,
        '7 - 7:59 p.m.'        : 19,
        'After 8 p.m.'         : None}
#############################################################################################################
dep_time_dist = readDistributionCDFs(os.path.join(os.path.dirname(os.path.realpath(__file__)), "DepartureTimeCDFs.dat"))

df = pd.read_csv('OBSdata_wBART_wSFtaz.csv',
                  dtype={"onoff_enter_station":object,
                         "onoff_exit_station" :object,
                         "persons"            :object,
                         "ID"                 :object,
                         "approximate_age"    :float,  # really should be int but there are missing values
                         "depart_hour"        :object,
                         "return_hour"        :object},
                  na_values=["missing","Missing","refused"])
print "Read %d trips" % len(df)

#Removing unnecessary columns
df = df [['workers','vehicles','Unique_ID','ID','access_mode','depart_hour','return_hour','day_part','weekpart','egress_mode','fare_category','fare_medium','gender','household_income','persons','work_status','approximate_age','tour_purp','path_line_haul','dest_maz','dest_sf_taz','orig_maz','orig_sf_taz']]

# Remove weekend trips
df = df[ df['weekpart']=='WEEKDAY' ]
print "Removed weekend trips, and filtered to %d trips" % len(df)

# rename
df.rename(columns={"orig_sf_taz":"o_taz",
                   "dest_sf_taz":"d_taz"}, inplace=True)

#### Make hhveh strings with numbers ("2" instead of "two")
df["hh_vehicles"] = df["vehicles"].replace(Num_dict)

#### Pick midpoint for household income (keep as string)
# handle commas or none
for inc_range in Inc_dict.keys():
      inc_value = Inc_dict[inc_range]
      inc_range = string.replace(inc_range, ",", "")
      Inc_dict[inc_range] = inc_value
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
df["transit_pass"] = 0
df.loc[ df["fare_medium first_word"].isin(pass_media), "transit_pass"] = 1

#### set disability based on fare_categ
df["disability"] = "none"
df.loc[df["fare_category"]=="disabled", "disability"] = "unknown disability"
# what about the "senior or disabled" fare_category?

#### remap purpose
df["purpose"] = df["tour_purp"].replace(purp_dict)
# set unknown purpose to "other"
df["purpose"].fillna("other", inplace=True)

#### clean access and egress modes
# assume walk for missing
df["access_mode"].fillna("walk", inplace=True)
df["egress_mode"].fillna("walk", inplace=True)
# capitalize knr, pnr and call "." walk
df["access_mode"] = df["access_mode"].replace(AccEgrs_dict)
df["egress_mode"] = df["egress_mode"].replace(AccEgrs_dict)

#### create mode
df["mode"] = df["access_mode"] + "-transit-" + df["egress_mode"]

#### create departure and arrival time based on depart_hour and return_hour
# create departure/arrival column = departure/arrival time in minutes after midnight
df["departure"]      = df["depart_hour"].map(lambda x: chooseTimeFromDistribution(dep_time_dist[x]), na_action='ignore')
df["departure_time"] = df["departure"].map(lambda x: convertTripTime(x), na_action='ignore')
df["arrival"]        = df["return_hour"].map(lambda x: chooseTimeFromDistribution(dep_time_dist[x]), na_action='ignore')
df["arrival_time"]   = df["arrival"].map(lambda x: convertTripTime(x), na_action='ignore')
#df["time_target"]    = "departure"           # don't know

#### create time_target
# create survey_start_hr
# BART
BART = pd.read_csv('BART_TimeStartedSurvey.csv',
                    na_values=['Missing - Question Not Asked','Missing - Dummy Record'])
BART['Unique_ID'] = BART['ID'].astype(str) + '---BART---2015'
BART['survey_start_hr'] = BART['Q1_START'].astype(str).str.split(' ').str.get(1).str.split(':').str.get(0)
BART = BART[['Unique_ID','survey_start_hr']]
# Caltrain
Caltrain = pd.read_csv('Caltrain_TimeStartedSurvey.csv')
Caltrain['Unique_ID'] = Caltrain['ID'].astype(str) + '---Caltrain---2014'
Caltrain = Caltrain [Caltrain['TIME SURVEY BEGAN'].notnull()]
Caltrain['survey_start_hr'] = Caltrain['TIME SURVEY BEGAN'].astype(str).str.split(':').str.get(0).astype(int)
Caltrain['tp'] = Caltrain['TIME SURVEY BEGAN'].astype(str).str.split(' ').str.get(1)
Caltrain.loc[ (Caltrain['tp']!='pm')&(Caltrain['survey_start_hr']!=12), 'survey_start_hr'] = Caltrain['survey_start_hr']+12
Caltrain = Caltrain[['Unique_ID','survey_start_hr']]
# NapaVine
NapaVine = pd.read_csv('NapaVINE_TimeStartedSurvey.csv')
NapaVine['Unique_ID'] = NapaVine['ID'].astype(str) + '---Napa Vine---2014'
NapaVine['survey_start_hr'] = NapaVine['TIME_BOARDED'].replace(hours)
NapaVine = NapaVine[['Unique_ID','survey_start_hr']]
# TriDelta
TriDelta = pd.read_csv('TriDelta_TimeStartedSurvey.csv')
TriDelta['Unique_ID'] = TriDelta['ID'].astype(str) + '---Tri-Delta---2014'
TriDelta['survey_start_hr'] = TriDelta['TIME_BOARDED'].replace(hours)
TriDelta = TriDelta[['Unique_ID','survey_start_hr']]
# put them all together and merge with df
survey_start_hr_df = pd.concat([BART, Caltrain, NapaVine, TriDelta], axis=0)
survey_start_hr_df = survey_start_hr_df.loc[ pd.notnull(survey_start_hr_df['survey_start_hr']) ]
df = pd.merge(df,survey_start_hr_df,how='left',on='Unique_ID')

# create dep_hr and arr_hr as integer, and put 99 for NaN
df['dep_hr'] = df['depart_hour'].fillna(99).astype(int)
df['arr_hr'] = df['return_hour'].fillna(99).astype(int)
df['survey_start_hr'] = df['survey_start_hr'].fillna(99).astype(int)
# set time_target based on survey_time, and allow for up to 3 hour deviations, b/c
# it's not unreasanable if e.g. one departed home at 6:55 (depart_hr=6), and
# being surveyed at 9:03 (survey_start_hr=9).
df['time_target'] = None
hr_diff = 0
while (hr_diff <=3):
    df.loc[ (df['dep_hr']==df['survey_start_hr'])&(df['time_target'].isnull())&(df['dep_hr']<90), 'time_target'] = 'departure'
    df.loc[ (df['arr_hr']==df['survey_start_hr'])&(df['time_target'].isnull())&(df['arr_hr']<90), 'time_target'] = 'arrival'
    print "set time_target for", len(df[df['time_target'].notnull()]), "trips, with hr_diff=", hr_diff
    hr_diff = hr_diff+1
    # continue only for those with null time_target to avoid overwriting
    df.loc[ df['time_target'].isnull(), 'dep_hr'] = df['dep_hr']+hr_diff
    df.loc[ df['time_target'].isnull(), 'arr_hr'] = df['arr_hr']-hr_diff
# For those without survey_start_hr, try the same process using time periods
df['dep_hr'] = df['depart_hour'].fillna(99).astype(int)
df['arr_hr'] = df['return_hour'].fillna(99).astype(int)
df['dep_tp'] = df['dep_hr'].replace(survey_time_period)
df['arr_tp'] = df['arr_hr'].replace(survey_time_period)
hr_diff = 0
while (hr_diff <=3):
    df.loc[ (df['survey_start_hr']>90)&(df['dep_tp']==df['day_part'])&(df['time_target'].isnull()), 'time_target'] = 'departure'
    df.loc[ (df['survey_start_hr']>90)&(df['arr_tp']==df['day_part'])&(df['time_target'].isnull()), 'time_target'] = 'arrival'
    print "set time_target for", len(df[df['time_target'].notnull()]), "trips, using time period with hr_diff=", hr_diff
    hr_diff = hr_diff+1
    df.loc[ df['time_target'].isnull(), 'dep_tp'] = (df['dep_hr']+hr_diff).replace(survey_time_period)
    df.loc[ df['time_target'].isnull(), 'arr_tp'] = (df['arr_hr']-hr_diff).replace(survey_time_period)
# For now, ssume "departure" for those we don't know
df.loc[ df['time_target'].isnull(), "time_target" ] = "departure"

#### Value of Time
'''VoT based on SFCTA RPM-9 Report, p39:
- non-work VoT = 2/3 work VoT,
- Impose a minimum of $1/hr and a maximum of $50/hr,
- Impose a maximum of $5/hr for workers younger than 18 years old.'''
df["vot"] = -1.0   # define it as float type
df.loc[ (df["age"]<=18)&(df["worker_status"]=='full-time'),            "vot"] = 5.0  # max $5 for workers under than 18 years old
df.loc[ pd.isnull(df["hh_income"])|(df["worker_status"]!='full-time'), "vot"] = 1.0  # $1 for non-workers

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
print "Removed trips with missing o/d taz, and filtered to %d trips" % len(df)

df["hh_id num"] = df.index + 1
df["hh_id"] = df["hh_id num"].map(lambda x: "hh%d" % x)
df["person_id"] = df["Unique_ID"]
# Since person_ids are unique, person_trip_id can just be 0
df["person_trip_id"] = 0

# write out the relevant columns
household_df = df[['hh_id','hh_vehicles','hh_income','hh_size','hh_workers']]
household_df.to_csv("household.txt", index=False)

persons_df = df[['person_id','hh_id','age','gender','worker_status','transit_pass','disability']]
persons_df.to_csv("person.txt", index=False, float_format="%.0f")

trips_df = df[['person_id','person_trip_id','o_taz','d_taz','mode','purpose','departure_time','arrival_time','time_target','vot']]
trips_df.sort_values(by=["person_id"]).to_csv("trip_list.txt", index=False, float_format="%.2f")

print "Done!"