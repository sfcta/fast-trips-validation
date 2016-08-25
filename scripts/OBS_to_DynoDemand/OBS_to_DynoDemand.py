###################################################################################
# Converts on-board survey data to Dyno-Demand files
# Reads: OBSdata_wBART_wSFtaz.csv, DepartureTimeCDFs.dat
# Writes: household.txt, person.txt, trip_list.txt
##########################################################################################################
import pandas as pd
from util_functions import *

Num_dict = {'zero':'0', 'one':'1', 'two':'2', 'three':'3', 'four':'4', 'five':'5', 
            'six':'6', 'seven':'7', 'eight':'8', 'nine':'9', 'ten':'10',
            'eleven':'11', 'twelve':'12', 'thirteen':'13', 'fourteen':'14', 'fifteen':'15',
            'four or more':'4', 'six or more':'6', 'ten or more':'10',
            'other':'', 'NA':''}

Inc_dict = {'$10000 to $25000':'17500', '$25000 to $35000':'30000', '$35000 to $50000':'42500', 
            '$50000 to $75000':'62500', '$75000 to $100000':'87500', '$100000 to $150000':'125000', 
            '$35000 or higher':'35000', 'under $35000':'18000', 'under $10000':'5000',
            '$150000 or higher':'150000', 'NA':'', 'refused':''}

work_status = ['full- or part-time', 'non-worker']
work_dict = {'full- or part-time':'full-time', 'non-worker':'unemployed'}

#Purposes are translated such that they align with those configured for pathweights
purp_dict = {'at work':'work', 'work':'work', 'work-related':'work_based', 'home':'work', 'college':'college', 
            'university':'college', 'school':'high_school', 'high school':'high_school', 'grade school':'grade_school', 
            'escorting':'grade_school', 'eat out':'other', 'shopping':'other', 'social recreation':'other', 
            'other maintenance':'other', 'other discretionary':'other', 'missing':'', 'NA':''}

pass_media = ['Clipper','clipper','pass','exempt']

AccEgrs_dict = {'bike':'bike', 'walk':'walk', 'pnr':'PNR', 'knr':'KNR', 'NA':'walk', '.':'walk'}
MainMode_dict = {'COM':'commuter_rail', 'EXP':'express_bus', 'LOC':'local_bus', 'HVY':'heavy_rail',
                'LRF':'light_rail', 'NA':'transit'}
#############################################################################################################
dep_time_dist = readDistributionCDFs("DepartureTimeCDFs.dat")
df = pd.read_csv('OBSdata_wBART_wSFtaz.csv')

#Removing unnecessary columns
df = df [['workers','vehicles','ID','access_mode','depart_hour','egress_mode','fare_category','fare_medium','gender','household_income','persons','work_status','approximate_age','tour_purp','path_line_haul','dest_maz','dest_sf_taz','orig_maz','orig_sf_taz']]
df = df.fillna(value='NA')
df.replace('missing','NA',inplace=True)
df.replace('Missing','NA',inplace=True)

hh_out = pd.DataFrame(); per_out = pd.DataFrame(); trip_out = pd.DataFrame()
for i in range(len(df)):
    print i
    hhVeh = Num_dict[df['vehicles'][i]]
    hhInc = Inc_dict[df['household_income'][i]]
    hhSize = Num_dict[df['persons'][i]]
    hhWorkers = Num_dict[df['workers'][i]]
    perID = df['ID'][i]
    
    if df['gender'][i]=='NA': gender = ''
    else: gender = df['gender'][i]
    
    if 6 <= df['approximate_age'][i] <= 110: age = int(df['approximate_age'][i])
    else: age = ''
    
    if df['work_status'][i] in work_status: work = work_dict[df['work_status'][i]]
    else: work = ''
    
    if df['fare_medium'][i]=='NA' or df['fare_medium'][i]=='Missing': trnPass = ''
    elif df['fare_medium'][i].split(' ')[0] in pass_media: trnPass = '1'
    else: trnPass = '0'
        
    if df['fare_category'][i]=='disabled': disability = 'unknown disability'
    else: disability = 'none'
        
    if df['orig_sf_taz'][i]=='NA': oTAZ = ''
    else: oTAZ = df['orig_sf_taz'][i]
    
    if df['dest_sf_taz'][i]=='NA': dTAZ = ''
    else: dTAZ = df['dest_sf_taz'][i]
    
    purp = purp_dict[df['tour_purp'][i]]
    mode = AccEgrs_dict[df['access_mode'][i]] + '-transit-' + AccEgrs_dict[df['egress_mode'][i]]
        
    if df['depart_hour'][i] == 'NA':
        departTime = ''
    else:
        departure = chooseTimeFromDistribution( dep_time_dist[ str(int(df['depart_hour'][i])) ] )
        departTime = convertTripTime(departure)
                
    '''VoT based on SFCTA RPM-9 Report, p39:
    - non-work VoT = 2/3 work VoT,
    - Impose a minimum of $1/hr and a maximum of $50/hr,
    - Impose a maximum of $5/hr for workers younger than 18 years old.'''
    if age!='' and age<=18 and work=='full-time':
        vot = 5
    if hhInc=='' or work!='full-time':
        vot = 1
    elif (hhWorkers=='' or hhWorkers=='0'):   #For cases where we have the income but not the number of workers, assume there is 1 worker. 
        vot_w = float(hhInc)/(52*40)          # 52*40 : No. of hours worked per year
        if purp=='work': vot = min(50,vot_w)
        else: vot = min(50,round(0.67*vot_w,2))
    else:
        vot_w = (float(hhInc)/int(hhWorkers))/(52*40)
        if purp=='work': vot = min(50,round(vot_w,2))
        else: vot = min(50,round(0.67*vot_w,2))
            
    hh_str = [('hh'+str(i+1),hhVeh,hhInc,hhSize,hhWorkers,'','','','')]
    hh_out = hh_out.append(hh_str)
    per_str = [(perID,'hh'+str(i+1),age,gender,work,'','',trnPass,disability)]
    per_out = per_out.append(per_str)
    trip_str = [(perID,oTAZ,dTAZ,mode,purp,departTime,departTime,'departure',vot)]
    trip_out = trip_out.append(trip_str)
    '''Since OBS data does not contain arrival time, yet arrival time is not an optional column, we just copy departure time there.
    However, since time_target is set to be 'departure', arrival time won't be read.'''

hh_cols = ['hh_id','hh_vehicles','hh_income','hh_size','hh_workers','hh_presch','hh_grdsch','hh_hghsch','hh_elder']
hh_out.columns = hh_cols
hh_out.to_csv('household.txt',index=False)
per_cols = ['person_id','hh_id','age','gender','work_status','work_at_home','multiple_jobs','transit_pass','disability']
per_out.columns = per_cols
per_out.to_csv('person.txt',index=False)
trip_cols = ['person_id','o_taz','d_taz','mode','purpose','departure_time','arrival_time','time_target','vot']
trip_out.columns = trip_cols
trip_out.to_csv('trips_list.txt',index=False)

print "Done!"