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
			if not (line.isspace() or ("%" in line and (not "class" in line))):
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

	output_df = pd.DataFrame(columns=['distance_MM', 'distance_PM', 'distance_PP'])

	for fil_i, df_fil_i in temp_dataframe.groupby('identity'):
		fil_i_id=df_fil_i['identity'].values[0]
		# temp_dataframe.loc[(temp_dataframe.identity == fil_i_id), 'identity']=69
		fil_i_pos_M_arr=df_fil_i[['posMX', 'posMY']].values[0]
		fil_i_pos_P_arr=df_fil_i[['posPX', 'posPY']].values[0]

		for fil_j, df_fil_j in temp_dataframe.groupby('identity'):
			fil_j_id=df_fil_j['identity'].values[0]

			if fil_j_id > fil_i_id:
				fil_j_pos_M_arr=df_fil_j[['posMX', 'posMY']].values[0]
				fil_j_pos_P_arr=df_fil_j[['posPX', 'posPY']].values[0]

				distance_MM=np.linalg.norm(fil_i_pos_M_arr - fil_j_pos_M_arr)
				distance_PM=np.linalg.norm(fil_i_pos_P_arr - fil_j_pos_M_arr)
				distance_PP=np.linalg.norm(fil_i_pos_P_arr - fil_j_pos_P_arr)

				if distance_MM < distance_cutoff:
					output_df = output_df.append({'distance_MM' : float(distance_MM)}, ignore_index=True)

				if distance_PM < distance_cutoff:
					output_df = output_df.append({'distance_PM' : float(distance_PM)}, ignore_index=True)

				if distance_PP < distance_cutoff:
					output_df = output_df.append({'distance_PP' : float(distance_PP)}, ignore_index=True)

	df_MM=output_df.distance_MM.dropna()
	df_PM=output_df.distance_PM.dropna()
	df_PP=output_df.distance_PP.dropna()

	df_MM.to_csv(output_file_path.with_suffix('.distance_MM.dat'), header=False, index=None, sep="\t")
	df_PM.to_csv(output_file_path.with_suffix('.distance_PM.dat'), header=False, index=None, sep="\t")
	df_PP.to_csv(output_file_path.with_suffix('.distance_PP.dat'), header=False, index=None, sep="\t")

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
	# Performance profiling code
	#import timeit
	#print(timeit.repeat('main(sys.argv[1:])', setup="from __main__ import main",number=1,repeat=10))
	main(sys.argv[1:])
