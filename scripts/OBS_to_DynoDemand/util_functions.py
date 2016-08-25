import random

def readDistributionCDFs(filename):
    """
    Distribution files are of the format:
    timeperiod, startmin, CDF
    
    Returns a dictionary: timeperiod -> [ (startmin, CDF) ]
    """
    distribution = {}
    distrib_file = open(filename, mode="r")
    for line in distrib_file:
        if line[0] in ['*',"#",";"]: continue # comment
        
        fields = line.split(",")
        timeperiod = fields[0]
        if timeperiod not in distribution:
            distribution[timeperiod] = []
        
        distribution[timeperiod].append((int(fields[1]), float(fields[2])))
    distrib_file.close()
    
    return distribution

def chooseTimeFromDistribution(distribution):
    """
    Given a distribution, which is a CDF defined by a list of [ (startmin1, CDF1), (startmin2, CDF2), ...]
    chooses a time (an integer, minutes since the start of the day) and returns it.
        
    Return range is based on the distribution.
    """
        
    r = random.random() # in [0.0, 1.0)
    prev_cdf = 0.0
    
    for idx in range(len(distribution)):

        if prev_cdf < r < distribution[idx][1]:
            # we're done - pick a time within the 5 min window
            return int(distribution[idx][0] + (r-prev_cdf)*(5.0)/(distribution[idx][1]-prev_cdf))
                
        prev_cdf = distribution[idx][1]

    raise Exception("chooseTimeFromDistribution: should never get here")

def convertTripTime(triptime):
    if int(triptime) > 0:
        hour = int(triptime/60)
        minute = triptime % 60
        return '%02d:%02d:00' %(hour,minute)
    else:
        return ''