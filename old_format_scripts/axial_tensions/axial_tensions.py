#!/usr/bin/python
"""Usage:
python /path/to/axial-tensions.py -i forces.txt

The forces.txt file is generated using a custom Cytosim report function:
report2 fiber:forces

i.e.:

singularity exec /path/to/cytosim_sandbox.sif /home/cytosim/bin/report2 fiber:forces frame=1000 > forces.txt

For cluster data:
report2 fiber:cluster_fiber_position

Make sure the report is generated for the last frame only (not for all frames)

Output file name is automatically generated as ???.dat
Can specify a custom output file name with the -o flag

"""
import sys # for command line arguments
import argparse # for parsing command line arguments to script

# https://stackoverflow.com/a/42288083
from pathlib import Path # for stripping filename extensions

import os # for removing files

import pandas as pd # for processing data file

pd.set_option("display.max_rows", None, "display.max_columns", None)

import numpy as np

def get_args():
	"""Parse the command line input flags and arguments"""

	input_file_name = ''
	output_file_name = ''
	cluster_file_name = ''

	parser = argparse.ArgumentParser(description='')

	parser.add_argument('--ifile', '-i', type=str, help='')
	parser.add_argument('--ofile', '-o', type=str, help='')
	parser.add_argument('--clusters', '-c', type=str, help='')
	# https://stackoverflow.com/a/31347222
	parser.add_argument('--largest', default=True, action=argparse.BooleanOptionalAction, help='calculate tensions for filaments beloning to the largest cluster, ignore all other filaments')

	args = parser.parse_args()

	return args

def process_file(args):
	"""Open input file, make a copy, remove unnecessary lines, process data,
	write to output file
	"""
	input_file_name=args.ifile
	output_file_name=args.ofile
	cluster_file_name=args.clusters

	# If outputfile name not provided, replace/add suffix '.dat' to input file name
	if not output_file_name:
		input_file_path = Path(input_file_name)
		output_file_name = input_file_path.with_suffix('.dat')

	only_largest = args.largest

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
			if not (line.isspace() or ("%" in line and (not "identity" in line))):
				temp_file.write(line.replace("%",""))

	# Read the whitespace-delimited data file that is output by Cytosim
	temp_dataframe = pd.read_csv(temp_file_name, delim_whitespace=True)

	# If cluster data file was provided, add cluster data to dataframe
	if cluster_file_name:
		cluster_file_path = Path(cluster_file_name)
		cluster_temp_file_name = cluster_file_path.with_suffix('.tmp')
		cluster_temp_file_path = Path(cluster_temp_file_name)

		with open(cluster_file_name) as cluster_file, open(cluster_temp_file_name,'w') as temp_file:
				for line in cluster_file:
					if not (line.isspace() or ("%" in line and (not "fiber_id" in line))):
						temp_file.write(line.replace("%","").replace("fiber_id","identity"))

		# Retain information on filament id and cluster id only
		cluster_temp_dataframe = pd.read_csv(cluster_temp_file_name,delim_whitespace=True)[['cluster','identity']]

		if only_largest:
			largest_cluster_id = cluster_temp_dataframe['cluster'].value_counts().idxmax()

		# merge cluster id information into full dataframe
		# https://stackoverflow.com/a/65450775
		temp_dataframe = temp_dataframe.merge(cluster_temp_dataframe, on='identity')

	# Update the temp file, mostly for debugging.
	# File not used for calculations, calcs done with the dataframe object
	temp_dataframe.to_csv(temp_file_name, sep="\t", index=None)

	# Define output dataframe
	if cluster_file_name:
		output_df = pd.DataFrame(columns=['identity', 'tension', 'cluster'])
	else:
		output_df = pd.DataFrame(columns=['identity', 'tension'])

	# iterate over filament id and sum tensions
	for fil_id, df_filament in temp_dataframe.groupby('identity'):
		total_tension=df_filament['tension'].sum()
		cluster_id = df_filament['cluster'].values[0]

		if cluster_file_name:
			if only_largest:
				if cluster_id == largest_cluster_id:
					new_df = pd.DataFrame([[fil_id,total_tension]], columns=['identity','tension'])
					output_df =pd.concat([output_df, new_df], ignore_index=True)
			else:
				new_df = pd.DataFrame([[fil_id,total_tension,cluster_id]], columns=['identity','tension','cluster'])
				output_df =pd.concat([output_df, new_df], ignore_index=True)
		else:
			new_df = pd.DataFrame([[fil_id,total_tension]], columns=['identity','tension'])
			output_df =pd.concat([output_df, new_df], ignore_index=True)



	# Write to output file
	output_file_path = Path(output_file_name)
	output_df.to_csv(output_file_path, float_format='%.3f', header=False, index=None, sep="\t")

	try:
		os.remove(temp_file_path)
		if cluster_file_name:
			os.remove(cluster_temp_file_path)
	except OSError as e:  ## if failed, report it back to the user ##
		print ("Error: %s - %s." % (e.filename, e.strerror))

def main(argv):

	# Get file name(s) from command line arguments
	args = get_args()

	# Do the calculations and output results to file


	process_file(args)

if __name__ == "__main__":
	# Performance profiling code
	#import timeit
	#print(timeit.repeat('main(sys.argv[1:])', setup="from __main__ import main",number=1,repeat=10))
	main(sys.argv[1:])
