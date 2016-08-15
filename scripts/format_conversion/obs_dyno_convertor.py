###################################################################################
# Converts on-board survey data to Dyno-Demand files
# Created on June 3, 2016
# Reads: OBSdata.csv, DepartureTimeCDFs.dat
# Writes: household.txt, person.txt, trip_list.txt
##########################################################################################################
from util_functions import *

Num_dict = {'zero':'0', 'one':'1', 'two':'2', 'three':'3', 'four':'4', 'five':'5', 
			'six':'6', 'seven':'7', 'eight':'8', 'nine':'9', 'ten':'10',
			'eleven':'11', 'twelve':'12', 'thirteen':'13', 'fourteen':'14', 'fifteen':'15',
			'four or more':'4', 'six or more':'6', 'ten or more':'10',
			'other':'', 'NA':''}

Inc_dict = {'$10000 to $25000':'17500', '$25000 to $35000':'30000', '$35000 to $50000':'42500', 
			'$50000 to $75000':'62500', '$75000 to $100000':'87500', '$100000 to $150000':'125000', 
			'$150000 or higher':'150000',
			'$35000 or higher':'35000', 'under $35000':'35000', 'under $10000':'10000',
			'Missing':'', 'NA':'', 'refused':''}

work_status = ['full- or part-time', 'non-worker']
work_dict = {'full- or part-time':'full-time', 'non-worker':'unemployed'}

#Purposes are translated such that they align with those configured for pathweights
purp_dict = {'at work':'work', 'work':'work', 'work-related':'work_based',
			'college':'college', 'university':'college', 'school':'high_school',
			'high school':'high_school', 'grade school':'grade_school', 'escorting':'grade_school',
			'shopping':'other', 'social recreation':'other', 'eat out':'other',
			'other discretionary':'other', 'other maintenance':'other', 'NA':''}

pass_media = ['Clipper','clipper','pass','exempt']

AccEgrs_dict = {'bike':'bike','walk':'walk','pnr':'PNR','knr':'KNR','NA':'walk','.':'walk'}
MainMode_dict = {'COM':'commuter_rail','EXP':'express_bus','LOC':'local_bus','HVY':'heavy_rail',
				'LRF':'light_rail','NA':'transit'}
#############################################################################################################
dep_time_dist = readDistributionCDFs("DepartureTimeCDFs.dat")

inFile = open('OBSdata.csv')
LineIn = inFile.readline()

outFileHH = open("household.txt", "w")
outFileHH.write("hh_id,hh_vehicles,hh_income,hh_size,hh_workers,hh_presch,hh_grdsch,hh_hghsch,hh_elders\n")
outFilePrsn = open("person.txt", "w")
outFilePrsn.write("person_id,hh_id,age,gender,work_status,work_at_home,multiple_jobs,transit_pass,disability\n")
outFileTrp = open("trips_list.txt", "w")
outFileTrp.write("person_id,o_taz,d_taz,mode,purpose,departure_time,arrival_time,time_target,vot\n")

i=0
while(True):
    LineIn = inFile.readline()
    if(LineIn) == "":
        break
    else:
        i=i+1
        LnSplt = LineIn.split(",")
        hhVeh = Num_dict[LnSplt[4]]		#vehicles
        hhInc = Inc_dict[LnSplt[18]]	#household_income
        hhSize = Num_dict[LnSplt[25]]	#persons
        hhWorkers = Num_dict[LnSplt[3]]	#workers
        prsnID = LnSplt[5]				#ID
        gender = LnSplt[16]				#gender
        
        if LnSplt[38] in [7,100]:		#approximate_age
            age = LnSplt[38]
        else:
            age = ''
        
        if LnSplt[36] in work_status:	#work_status
            work = work_dict[LnSplt[36]]
        else:
            work = ''
        
        passStr = LnSplt[13].split(' ')	#fare_medium
        if passStr[0] in pass_media:
            trnPass = '1'
        else:
            trnPass = '0'
        
        if LnSplt[12]=='disabled':		#fare_category
            disability = 'unknown disability'
        else:
            disability = 'none'
        
        oTAZ = LnSplt[63]				#orig_taz
        dTAZ = LnSplt[61]				#dest_taz
        purp = purp_dict[LnSplt[39]]	#tour_purp
        
        depHr = LnSplt[7]				#depart_hour
        if depHr == 'NA':
            depTime = ''
        else:
            dep_time = chooseTimeFromDistribution(dep_time_dist[depHr])
            depTime = convertTripTime(dep_time)
        
        #access_mode + path_line_haul + egress_mode
        mode = AccEgrs_dict[LnSplt[6]] + '-transit-' + AccEgrs_dict[LnSplt[10]]
        #mode = AccEgrs_dict[LnSplt[6]] + '-' + MainMode_dict[LnSplt[47]] + '-' + AccEgrs_dict[LnSplt[10]]
        
        #VoT
        '''Based on SFCTA RPM-9 Report, p39:
        - non-work value of time = 2/3 work value of time,
        - Impose a minimum of $1/hour and a maximum of $50/hour,
        - Impose a maximum of $5/hour for workers younger than 18 years old.'''
        if age!='' and int(age)<=18 and work=='full-time':
            vot = 5
        if hhInc=='' or hhInc=='0' or work!='full-time':
            vot = 1
        elif (hhWorkers=='' or hhWorkers=='0'):		#For cases where we have the income but not the number of workers, assume there is 1 worker. 
            vot_w = float(hhInc)/(52*40)			# 52*40 : No. of hours worked per year
            if purp=='work': vot = min(50,vot_w)
            else: vot = min(50,round(0.67*vot_w,2))
        else:
            vot_w = (float(hhInc)/int(hhWorkers))/(52*40)
            if purp=='work': vot = min(50,round(vot_w,2))
            else: vot = min(50,round(0.67*vot_w,2))
            
        strOutHH = "hh" + str(i) + "," + hhVeh + "," + hhInc + "," + hhSize + "," + hhWorkers + ",,,,\n"
        outFileHH.write(strOutHH)
        strOutPrsn = prsnID + ",hh" + str(i) + "," + age + "," + gender + "," + work + ",,," + trnPass + "," + disability + "\n"
        outFilePrsn.write(strOutPrsn)
        strOutTrp = prsnID + "," + oTAZ + "," + dTAZ + "," + mode + "," + purp + "," + depTime + "," + depTime + "," + "departure," + str(vot) + "\n"
        '''Since OBS data does not contain arrival time, yet arrival time is not an optional column, we just copy departure time there.
		   However, since time_target is set to be 'departure', arrival time won't be read.'''
        outFileTrp.write(strOutTrp)

inFile.close()
outFileHH.close()
outFilePrsn.close()
outFileTrp.close()
print "Done!"