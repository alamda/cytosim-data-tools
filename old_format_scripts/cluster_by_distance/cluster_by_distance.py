#!/usr/bin/python
"""Usage:
python /path/to/cluster-by-distance.py -i position.txt

The position.txt file is generated using a custom Cytosim report function:
report2 fiber:position

i.e.:

singularity exec /path/to/cytosim_sandbox.sif /home/cytosim/bin/report2 fiber:position frame=1000 > positions.txt

Make sure the report is generated for the last frame only (not for all frames)

Output file name is automatically generated as ???.dat
Can specify a custom output file name with the -o flag

"""

import sys # for command line arguments
import getopt # for option flags for command line arguments

# https://stackoverflow.com/a/42288083
from pathlib import Path # for stripping filename extensions

import os # for removing files

import pandas as pd # for processing data file

pd.set_option("display.max_rows", None, "display.max_columns", None)

import numpy as np

def get_file_names(argv):
	"""Parse the command line input flags and arguments"""

	# https://docs.python.org/3/library/getopt.html
	input_file_name = ''
	output_file_name = ''

	try:
		opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
	except getopt.GetoptError:
		# If no command line arguments are given, return usage message and exit
		print('test.py -i <inputfile> -o <outputfile>')
		sys.exit(2)

	for opt, arg in opts:
		if opt == '-h':
			# Print help info for argument usage
			print('test.py -i <inputfile> -o <outputfile>')
			sys.exit()
		elif opt in ("-i", "--ifile"):
			input_file_name = arg
		elif opt in ("-o", "--ofile"):
			output_file_name = arg

	# If outputfile name not provided, replace/add suffix '.dat' to input file name
	if not output_file_name:
		input_file_path = Path(input_file_name)
		output_file_name = input_file_path.with_suffix('.dat')

	return (input_file_name, output_file_name)

def process_file(input_file_name, output_file_name):
	"""Open input file, make a copy, remove unnecessary lines, process data,
	write to output file
	"""

	# Copy input file to a temporary file which will be modified
	# (modifications: remove lines and columns with irrelevant comments and data)

	input_file_path = Path(input_file_name)
	temp_file_name = input_file_path.with_suffix('.tmp')
	temp_file_path = Path(temp_file_name)

	### Pre-process input data in temp file ###

	# Remove blank lines and lines with % (Cytosim comments)
	# BUT Keep line with column headers
	# https://stackoverflow.com/a/11969474 , https://stackoverflow.com/a/2369538
	with open(input_file_name) as input_file, open(temp_file_name, 'w') as temp_file:
		for line in input_file:
			if not (line.isspace() or ("%" in line and (not "posX" in line))):
				temp_file.write(line.replace("%",""))

	# Read the whitespace-delimited data file that is output by Cytosim
	temp_dataframe = pd.read_csv(temp_file_name, delim_whitespace=True)

	# Update the temp file, mostly for debugging.
	# File not used for calculations, calcs done with the dataframe object
	temp_dataframe.to_csv(temp_file_name, sep="\t", index=None)

	### Write to output file ###
	output_file_path = Path(output_file_name)

	cluster_idx = 0

	fil_length=0.25

	distance_cutoff=fil_length*2

	# initialize the cluster id for all filaments (sequentially)

	num_filaments=temp_dataframe.shape[0]
	init_cluster_ids = np.arange(0,num_filaments)

	temp_dataframe['cluster']=init_cluster_ids


	for fil_i, df_fil_i in temp_dataframe.groupby('identity'):
		fil_i_id=df_fil_i['identity'].values[0]
		# temp_dataframe.loc[(temp_dataframe.identity == fil_i_id), 'identity']=69
		fil_i_pos_arr=df_fil_i[['posX', 'posY']].values[0]

		fil_i_cluster_id=df_fil_i['cluster'].values[0]

		for fil_j, df_fil_j in temp_dataframe.groupby('identity'):
			fil_j_id=df_fil_j['identity'].values[0]

			if fil_j_id > fil_i_id:
				fil_j_pos_arr=df_fil_j[['posX', 'posY']].values[0]

				fil_j_cluster_id=df_fil_j['cluster'].values[0]

				distance=np.linalg.norm(fil_i_pos_arr-fil_j_pos_arr)

				if distance < distance_cutoff:
					min_cluster_id=min(fil_i_cluster_id, fil_j_cluster_id)
					# print(min_cluster_id)

					temp_dataframe.loc[(temp_dataframe.identity == fil_i_id), 'cluster']=min_cluster_id
					temp_dataframe.loc[(temp_dataframe.identity == fil_j_id), 'cluster']=min_cluster_id

	new_cluster_idx = 0

	# temp_dataframe=temp_dataframe.sort_values(by='cluster')
	temp_dataframe['cluster_size'] = temp_dataframe.groupby('cluster')['cluster'].transform(pd.Series.count)
	temp_dataframe=temp_dataframe.sort_values('cluster_size', ascending=False)

	for cluster, df_cluster in temp_dataframe.groupby('cluster'):
		old_cluster_idx=df_cluster['cluster'].values[0]
		temp_dataframe.loc[(temp_dataframe.cluster == old_cluster_idx), 'cluster'] = new_cluster_idx
		new_cluster_idx+=1

	# temp_dataframe.to_csv(output_file_path.with_suffix('.distance_cluster.dat'), header=True, index=None, sep="\t")

	# print(temp_dataframe.cluster.values[:])
	# ### Perform radius of gyration calculations ###
	#
	output_df = pd.DataFrame(columns=['cluster_size', 'radius_of_gyration'])

	for cluster, df_cluster in temp_dataframe.groupby('cluster'):
		# For each cluster, calculate the center of mass

		pos_array = df_cluster[['posX','posY']].values

		mass = 0

		COM_coords = np.zeros(pos_array[0].shape)

		for value in pos_array:
			mass += 1
			COM_coords += value

		COM_coords /= mass

		num_pts = 0

		radius_gyr_sq = 0

		for value in pos_array:
			num_pts += 1
			radius_gyr_sq += (np.linalg.norm(value - COM_coords))**2

		radius_gyr_sq /= num_pts

		radius_gyr = np.sqrt(radius_gyr_sq)

		cluster_size = df_cluster.shape[0]

		# add values to data frame which will be written to the output file
		output_df = output_df.append({'cluster_size' : int(cluster_size), \
				'radius_of_gyration' : radius_gyr},\
				 ignore_index=True)

	output_df.sort_values(by='cluster_size',ascending=False).to_csv(output_file_path.with_suffix('.rad_gyr.dat'), header=False, index=None, sep="\t")

	output_df = pd.DataFrame(columns=['filament_pair_angle', 'cluster_id'])
	output_df_largest_cluster = pd.DataFrame(columns=['filament_pair_angle'])
	output_df_sin = pd.DataFrame(columns=['filament_pair_sin_theta', 'cluster_id'])
	output_df_sin_largest_cluster = pd.DataFrame(columns=['filament_pair_sin_theta'])

	first_cluster=True

	for cluster, df_cluster in temp_dataframe.groupby('cluster'):

		for fil_i, df_fil_i in df_cluster.groupby('identity'):
			fil_i_id=df_fil_i['identity'].values[0]
			fil_i_dir_arr = df_fil_i[['dirX', 'dirY']].values[0]

			for fil_j, df_fil_j in df_cluster.groupby('identity'):
				fil_j_id=df_fil_j['identity'].values[0]

				if fil_j_id > fil_i_id:

					fil_j_dir_arr = df_fil_j[['dirX', 'dirY']].values[0]

					theta=np.arccos(np.dot(fil_i_dir_arr/np.linalg.norm(fil_i_dir_arr), fil_j_dir_arr/np.linalg.norm(fil_j_dir_arr)))

					sin_theta = np.sin(theta)

					# add values to data frame which will be written to the output file
					output_df = output_df.append({'filament_pair_angle' : float(theta), \
												  'cluster_id' : int(cluster)},\
												 ignore_index=True)
					output_df_sin = output_df_sin.append({'filament_pair_sin_theta' : float(sin_theta), 'cluster_id' : int(cluster)}, ignore_index=True)

					if first_cluster:
						output_df_largest_cluster = \
							output_df_largest_cluster.append({'filament_pair_angle' : float(theta)}, ignore_index=True)
						output_df_sin_largest_cluster = output_df_sin_largest_cluster.append({'filament_pair_sin_theta' : float(sin_theta)}, ignore_index=True)

		first_cluster=False

	output_df.to_csv(output_file_path.with_suffix('.pair_angle_cluster.dat'), header=True, index=None, sep="\t")

	output_df_largest_cluster.to_csv(output_file_path.with_suffix('.pair_angle_cluster_largest.dat'), header=False, index=None, sep="\t")
	output_df_sin.to_csv(output_file_path.with_suffix('.pair_sin_theta_cluster.dat'), header=True, index=None, sep="\t")
	output_df_sin_largest_cluster.to_csv(output_file_path.with_suffix('.pair_sin_theta_cluster_largest.dat'), header=False, index=None, sep="\t")

	try:
		os.remove(temp_file_path)
	except OSError as e:  ## if failed, report it back to the user ##
		print ("Error: %s - %s." % (e.filename, e.strerror))

def main(argv):

	# Get file name(s) from command line arguments
	(input_file_name, output_file_name) = get_file_names(argv)

	# Do the calculations and output results to file
	process_file(input_file_name, output_file_name)

if __name__ == "__main__":
	main(sys.argv[1:])
