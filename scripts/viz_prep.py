import sys, os
import pandas as pd

USAGE = """
  python viz_prep.py model_results observed_records output_directory
  Appends observed to modeled Fast-Trips route choice data.
  Note: only common person-trip records are joined

  Output is stored at specified output_directory
"""

def append(*args):
	'''Union dataframes with similar structures'''
	df = pd.DataFrame()
	for data in args:
		df = df.append(data)

	return df

def prep_df(data, record_type, unique_fields ,colname='record_type'):
	'''Load text data as df, create unique trip record ID, and tag as model/observed record'''
	df = pd.read_csv(data)
	df[colname] = record_type    # tag as model/observed record
	
	# Convert all specified unique_fields to string and concatenate as new unique_id field 
	df[unique_fields] = pd.DataFrame([df[col].astype('str') for col in unique_fields]).T
	df['unique_id'] = df[unique_fields].apply(lambda x: ''.join(x), axis=1)

	return df

def select_common_records(df1,df2,field):
	'''Return dataframe of matching, common records only.
       Example, person 1034 exists in df1, but not in df2, so new copy of df1 without 1034 is created
	'''
	df1 = df1[df1[field].isin(df2[field])]
	df2 = df2[df2[field].isin(df1[field])]

	return df1, df2

if __name__ == "__main__":

    if len(sys.argv) != 4:
        print USAGE
        print sys.argv
        sys.exit(2)

    model_records = sys.argv[1]
    observed_records = sys.argv[2]
    OUTPUT_DIR = sys.argv[3]

    model = prep_df(data=model_records, record_type='model', unique_fields=['person_id','trip_list_id_num'])
    observed = prep_df(data=observed_records, record_type='observed', unique_fields=['person_id','trip_list_id_num'])

    model, observed = select_common_records(model,observed,'person_id')

    df = append(model, observed)

    df.to_csv(OUTPUT_DIR,index=False)

    print "Script complete, output stored in: %s" % OUTPUT_DIR