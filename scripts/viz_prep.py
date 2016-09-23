import sys, os
import pandas as pd

USAGE = """
  python viz_prep.py observed_records_file output_directory
  Appends observed to modeled Fast-Trips route choice data.
  Note: only common person-trip records are joined

  Output is stored at specified output_directory. FT output is also pulled from the same location
  so be sure the output directory contains complete FT output files
"""

# Parameters
# ===================================================
# Probability threshold for observed paths 
# e.g. are observed paths assigned above/below this value by fast-trips?
threshold = 0.3

# Compare observed path to pathset based on modes, agency, route, or all components (including stops)
# options: 'path_agencies', 'path_modes', 'path_routes', 'path_components'
comparison_field = 'path_agencies' 

non_transit_modes = ['transfer','walk_access','walk_egress','bike_access','bike_egress',
                     'PNR_access','PNR_egress','KNR_access','KNR_egress']



# Script
# ===================================================

def append(*args):
    '''Union dataframes with similar structures'''
    df = pd.DataFrame()
    for data in args:
        df = df.append(data)

    return df

def load_df(data, unique_fields, record_type=None):
    '''Load text data as df, create unique trip record ID, and tag as model/observed record'''
    df = pd.read_csv(data)
    if record_type != None:
        df['record_type'] = record_type    # tag as model/observed record

    # Convert all specified unique_fields to string and concatenate as new unique_id field 
    df[unique_fields] = pd.DataFrame([df[col].astype('int').astype('str') for col in unique_fields]).T
    df['unique_id'] = df[unique_fields].apply(lambda x: '_'.join(x), axis=1)

    return df

def select_common_records(df1,df2,field):
    '''Return dataframe of matching, common records only.
       Example, person 1034 exists in df1, but not in df2, so new copy of df1 without 1034 is created
    '''
    df1 = df1[df1[field].isin(df2[field])]
    df2 = df2[df2[field].isin(df1[field])]

    return df1, df2

def add_transit_agency(df, routes):

	df = pd.merge(left=df,right=routes[['route_id','agency_id']],on='route_id',how='left')
	
	df['agency'] = df['agency_id']
	df.drop('agency_id',axis=1)
	df.fillna("",inplace=True)
	df.reset_index(inplace=True)

	return df

def produce_path_fields(df, group):
    '''
    Concatenate set of fields for pathset_links, e.g. ('bart caltrain') for 2-leg transit trip
    Produce concatenated fields for routes, modes, agencies, all components (stops, modes, & routes)
    '''
    # create "path_routes"

    for field in ['route_id','mode','agency','A_id','B_id']:
    	df[field] = df[field].astype('str')
    	df[field] = df[field].fillna("")
    	df[field] = df[field].replace('nan',"")

    df['path_routes'] = df['route_id'].apply(lambda x: x.strip())
    path_routes = pd.DataFrame(df.groupby(group)['path_routes'].apply(lambda x: "%s" % ' '.join(x).strip()))
    
    result_df = pd.DataFrame(index=path_routes.index)
    result_df['path_routes'] = path_routes
    
    # create "path_modes"
    df['path_modes'] = df['mode'].apply(lambda x: x.strip())
    result_df['path_modes'] = pd.DataFrame(df.groupby(group)['mode'].apply(lambda x: "%s" % ' '.join(x).strip()))
    
    # create "path_agencies"
    df['path_agencies'] = df['agency'].apply(lambda x: x.strip())
    result_df['path_agencies'] = pd.DataFrame(df.groupby(group)['agency'].apply(lambda x: "%s" % ' '.join(x).strip()))

    # Create "path_components"
    df['path_components'] = df['A_id']+" "+df['mode']+" "+df['route_id'] +"_"+ df['B_id']
    df['path_components'] = df['path_components'].apply(lambda x: x.strip())
    result_df['path_components'] = pd.DataFrame(df.groupby(group)['path_components'].apply(lambda x: "%s" % ' '.join(x).strip()))
    
    # Return ID field from index
    result_df['unique_id'] = result_df.index.get_level_values(0).values

    return result_df

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print USAGE
        print sys.argv
        sys.exit(2)

    observed_records = sys.argv[1]
    OUTPUT_DIR = sys.argv[2]

    # Load data
    # ===================================================

    # NOTE: this should be taken from a FT network standard as an arg
    routes = pd.read_csv(r'../data/gtfs/routes.txt')
    
    # Load observed and chosenpath_links; add new field designating 'model' or 'observed'
    obs = load_df(data=observed_records, unique_fields=['person_id','trip_list_id_num'], record_type='observed', )
    chosenpath_links = load_df(data=OUTPUT_DIR + r'\chosenpaths_links.csv', 
    	unique_fields=['person_id','trip_list_id_num'], record_type='model', )
    # Only load the final iteration
    chosenpath_links = chosenpath_links[chosenpath_links['iteration'] == chosenpath_links['iteration'].max()]

    # Load pathset_links, final model iteration only for now
    pathset_links = load_df(data=OUTPUT_DIR + r'\pathset_links.csv', unique_fields=['person_id','trip_list_id_num'])
    pathset_links = pathset_links[pathset_links['iteration'] == pathset_links['iteration'].max()]

    pathset_paths = load_df(OUTPUT_DIR + r'\pathset_paths.csv', unique_fields=['person_id','trip_list_id_num'])

    # Clean data
    # ===================================================

   	# Create a stacked csv of observed trip links & model chosenpath_links; export for Tableau
    chosenpath_links, obs = select_common_records(chosenpath_links, obs,'person_id')
    append(chosenpath_links, obs).to_csv(OUTPUT_DIR + '/' + 'chosenpaths_links_with_observed.csv',index=False)

    # Add transit agency field to chosenpath_links and pathset_links, based on route_id
    chosenpath_links = add_transit_agency(df=chosenpath_links, routes=routes)
    pathset_links = add_transit_agency(df=pathset_links, routes=routes)
   
    # Analyze data
    # ===================================================
    
    # Produce concatenated path represenations for routes, modes, transit agencies
    observed_path = produce_path_fields(obs, group=['unique_id'])
    modeled_path = produce_path_fields(chosenpath_links, group=['unique_id'])

    # concat the detailed pathset_links files, so each path in the pathset has a unique trip identity
    pathset_links = produce_path_fields(pathset_links, group=['unique_id','pathnum'])
    

    # Make sure we only evaluate records that have unique_ids in common
    obs = obs[obs['unique_id'].isin(pathset_links['unique_id'].values)]
    pathset_links = pathset_links[pathset_links['unique_id'].isin(obs['unique_id'].values)]

	# Compare if modeled/observed trips match, completed or partially
	# Join the observed and modeled fields
    df = pd.merge(observed_path, modeled_path, on='unique_id',suffixes=("_observed","_model"))

    # Extract order of transit routes taken
    df['model_path_route_list'] = df['path_routes_model'].apply(lambda x: x.split(" "))
    df['obs_path_route_list'] = df['path_routes_observed'].apply(lambda x: x.split(" "))

    df['model_path_mode_list'] = df['path_modes_model'].apply(lambda x: x.split(" "))
    df['obs_path_mode_list'] = df['path_modes_observed'].apply(lambda x: x.split(" "))

    df['model_path_agencies_list'] = df['path_agencies_model'].apply(lambda x: x.split(" "))
    df['obs_path_agencies_list'] = df['path_agencies_observed'].apply(lambda x: x.split(" "))


    # Isolate transit modes only, because all trips should have walk & transfer components
    df['model_transit_modes'] = df['model_path_mode_list'].apply(
        lambda row: [element for element in row if element not in non_transit_modes])
    df['obs_transit_modes'] = df['obs_path_mode_list'].apply(
        lambda row: [element for element in row if element not in non_transit_modes])

    # Find the intersection between the chosen model/observed paths using different criteria
    # ===================================================

	# transit route IDs only
    df.apply(lambda row: all(i in row['model_path_route_list'] for i in row['obs_path_route_list']), axis=1)
    df['routes_intersection'] = [list(set(a).intersection(set(b))) for a, b in zip(df['model_path_route_list'], df['obs_path_route_list'])]

	# All Modes (including transfer, access/egress)
    df.apply(lambda row: all(i in row['model_path_mode_list'] for i in row['obs_path_mode_list']), axis=1)
    df['all_modes_intersection'] = [list(set(a).intersection(set(b))) for a, b in zip(df['model_path_mode_list'], df['obs_path_mode_list'])]

	# Transit modes only (type of vehicle taken and number of boardings)
    df.apply(lambda row: all(i in row['model_path_mode_list'] for i in row['obs_path_mode_list']), axis=1)
    df['transit_modes_intersection'] = [list(set(a).intersection(set(b))) for a, b in zip(df['model_transit_modes'], df['obs_transit_modes'])]

	# Agency Intersection
    df.apply(lambda row: all(i in row['model_path_agencies_list'] for i in row['obs_path_agencies_list']), axis=1)
    df['agency_intersection'] = \
	    [list(set(a).intersection(set(b))) for a, b in zip(df['model_path_agencies_list'], 
	        df['obs_path_agencies_list'])]

	# ===================================================
    # Find exact matches of routes, modes, and agencies between model and observed
    
    complete_route_match = df[df['path_routes_observed'] == df['path_routes_model']]
    complete_mode_match = df[df['path_modes_observed'] == df['path_modes_model']]
    complete_agency_match = df[df['path_agencies_observed'] == df['path_agencies_model']]
    
    # Add fields indicating complete match with 1
    complete_mode_match['complete_mode_match'] = 1
    complete_agency_match['complete_agency_match'] = 1
    complete_route_match['complete_route_match'] = 1

    # Add new columns to the larger dataframe indicating complete match
    df = pd.merge(df, complete_mode_match[['unique_id','complete_mode_match']], how='left', on='unique_id')
    df = pd.merge(df, complete_route_match[['unique_id','complete_route_match']], how='left', on='unique_id')
    df = pd.merge(df, complete_agency_match[['unique_id','complete_agency_match']], how='left', on='unique_id')

    # For fields without complete match, fill with 0
    for field in ['mode','route','agency']:
        df['complete_'+field+'_match']=  df['complete_'+field+'_match'].replace('nan',0)

    # Find % of trips with matching routes/modes/agencies, or partial matches

    # Number of records in common by field
    df['common_route_count'] = [len(row) for row in df['routes_intersection']]
    df['common_mode_count'] = [len(row) for row in df['all_modes_intersection']]
    df['common_transit_mode_count'] = [len(row) for row in df['transit_modes_intersection']]
    df['common_agency_count'] = [len(row) for row in df['agency_intersection']]

    # Do the fields have at least 1 component in common? 1 if yes, else 0
    df['partial_mode_match'] = [1 if row > 0 else 0 for row in df['common_mode_count']]
    df['partial_transit_mode_match'] = [1 if row > 0 else 0 for row in df['common_transit_mode_count']]
    df['partial_route_match'] = [1 if row > 0 else 0 for row in df['common_route_count']]
    df['partial_agency_match'] = [1 if row > 0 else 0 for row in df['common_agency_count']]

    # Export results of these comparisons
    df.to_csv(OUTPUT_DIR + '\path_intersection.csv', index=False)


    # Check if path is in pathset
    # ==========================================================

    ## Add a field to the new_pathset that lists the pathnum
    pathset_links['pathnum'] = pathset_links.index.get_level_values(1)

    # compare paths based on comparison_field, defined in script header

    df = pd.merge(observed_path, pathset_links, how='left',
              left_on=['unique_id',comparison_field],right_on=['unique_id',comparison_field], suffixes=['_obs','_pathset'])
    pathset_links.to_csv('test_pathset_links.csv')

    df[comparison_field + '_obs'] = df[comparison_field]
    df.drop(comparison_field, axis=1, inplace=True)

    df = (pd.merge(df, modeled_path[['unique_id',comparison_field]], how='left'))
    df[comparison_field + '_pathset'] = df[comparison_field]
    df.drop(comparison_field, axis=1, inplace=True)

    df['pathnum'] = df['pathnum'].fillna(0)
    df['pathnum'] = df['pathnum'].astype('int')

    newdf = pd.merge(df, pathset_paths, left_on=['unique_id','pathnum'], right_on=['unique_id','pathnum'])
    newdf['probability'] = newdf['probability'].fillna('no_match')

    newdf.to_csv('test_newdf.csv')

    max_prob = newdf.groupby('unique_id').max()['probability']
    min_prob = newdf.groupby('unique_id').min()['probability']

    prob_export = pd.DataFrame([max_prob,min_prob]).T
    prob_export.columns = ['max_prob','min_prob']

    # Pull binary data for each person
    prob_export['path_exists'] = prob_export['max_prob'].apply(lambda row_value: 0 if row_value == 'no_match' else 1)
    prob_export.to_csv('temp_prob_export.csv')

    # Mark no_match_records
    try:
	    prob_export.ix[prob_export['max_prob'] >= threshold, 'above_threshold'] = 1
	    prob_export.ix[prob_export['max_prob'] < threshold, 'above_threshold'] = 0
	    prob_export.ix[prob_export['max_prob'] == 'no_match', 'above_threshold'] = -1
    except:
	    pass

    # Join relevant columns and export
    prob_export['unique_id'] = prob_export.index
    export_df = pd.merge(df, prob_export, on='unique_id')
    export_df['person_id'] = export_df['unique_id'].apply(lambda row: row.split("_")[0])
    export_df['trip_list_id_num'] = export_df['unique_id'].apply(lambda row: row.split("_")[-1])

    export_df.to_csv(OUTPUT_DIR + '\path_comparison.csv', index=False)

    print "Script complete, output stored in: %s" % OUTPUT_DIR