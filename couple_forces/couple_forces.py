#!/usr/bin/python
"""Usage:
python /path/to/axial-tensions.py -i link_cluster.txt

The link_cluster.txt file is generated using a custom Cytosim report function:
report2 couple:link_cluster

i.e.:

singularity exec /path/to/cytosim_sandbox.sif /home/cytosim/bin/report2 fiber:forces frame=1000 > forces.txt

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

import pytest

def get_args(argv):
	"""Parse the command line input flags and arguments"""

	input_file_name = ''
	output_file_name = ''

	parser = argparse.ArgumentParser(description='')

	parser.add_argument('--ifile', '-i', type=str, help='')
	parser.add_argument('--ofile', '-o', type=str, help='')
	# https://stackoverflow.com/a/31347222
	parser.add_argument('--largest', default=True, action=argparse.BooleanOptionalAction, help='calculate forces exerted by couples attached to filaments beloning to the largest cluster, ignore all other couples')

	args = parser.parse_args(argv)

	return args

def get_file_paths(args):
	"""Generate the paths for the file names provided by args

	Return: file names + paths? as a dict?
	"""
	input_file_name=args.ifile
	output_file_name=args.ofile

	# If outputfile name not provided, replace/add suffix '.dat' to input file name
	if not output_file_name:
		input_file_path  = Path(input_file_name)
		output_file_path = input_file_path.with_suffix('.dat')
		output_file_name = output_file_path.name
	else:
		output_file_path = Path(output_file_name)

	# Copy input file to a temporary file which will be modified
	# (modifications: remove lines and columns with irrelevant comments and data)

	input_file_path = Path(input_file_name)
	temp_file_name = input_file_path.with_suffix('.tmp').name
	temp_file_path = Path(temp_file_name)

	input_dict = {"name": input_file_name, "path": input_file_path}
	output_dict = {"name": output_file_name, "path": output_file_path}
	temp_dict = {"name": temp_file_name, "path": temp_file_path}

	file_dict = {"input": input_dict, "output": output_dict, "temp": temp_dict}

	return file_dict

def preprocess_file(file_dict):
	"""Pre-process input data to remove extraneous (non-data or non-column
	header) lines.

	Returns: Pandas dataframe
	"""

	# Remove blank lines and lines with % (Cytosim comments)
	# BUT Keep line with column headers
	# https://stackoverflow.com/a/11969474 , https://stackoverflow.com/a/2369538
	with open(file_dict["input"]["path"]) as input_file, \
		 open(file_dict["temp"]["path"], 'w') as temp_file:
		for line in input_file:
			if not (line.isspace() or ("%" in line and (not "identity" in line))):
				temp_file.write(line.replace("%",""))

	# Read the whitespace-delimited data file that is output by Cytosim
	temp_dataframe = pd.read_csv(file_dict["temp"]["path"], delim_whitespace=True)

	# Check that data from only one simulation frame was loaded
	if temp_dataframe["identity"].isin(["identity"]).any():
		raise ValueError("Data for more than one frame loaded.")

	# Update the temp file, mostly for debugging.
	# File not used for calculations, calcs done with the dataframe object
	temp_dataframe.to_csv(file_dict["temp"]["path"], sep="\t", index=None)

	return temp_dataframe

def write_to_dataframe(output_df, couple_id, cluster_id, \
					   x1_force, y1_force, x2_force, y2_force, \
					   x1_force_sum, y1_force_sum, x2_force_sum, y2_force_sum):

	new_df1 = pd.DataFrame([[ couple_id, cluster_id, \
							  x1_force, y1_force ]],\
						      columns=[ 'identity', 'cluster',\
							   			'x1_force', 'y1_force' ])

	new_df2 = pd.DataFrame([[ couple_id, cluster_id, \
							  x2_force, y2_force ]],\
						  	  columns=[ 'identity', 'cluster', \
							  			'x2_force', 'y2_force' ])

	new_df_both = new_df1.merge(new_df2, on=["identity","cluster"])

	output_df = pd.concat([output_df, new_df_both], ignore_index=True)

	x1_force_sum += x1_force
	y1_force_sum += y1_force

	x2_force_sum += x2_force
	y2_force_sum += y2_force

	return (output_df, x1_force_sum, y1_force_sum, \
					   x2_force_sum, y2_force_sum )

def calc_force_vec(args, temp_dataframe):
	"""Open input file, make a copy, remove unnecessary lines, process data,
	write to output file

	Returns: Pandas dataframe
	"""
	only_largest = args.largest

	# Define output dataframe

	output_df = pd.DataFrame(columns=['identity', 'cluster', \
									  'x1_force', 'y1_force', \
									  'x2_force', 'y2_force'] )

	largest_cluster_id = temp_dataframe['cluster'].mode().values[0]

	x1_force_sum = 0
	y1_force_sum = 0

	x2_force_sum = 0
	y2_force_sum = 0

	# iterate over cluster id and find x and y components of force vector
	for couple_id, df_couple in temp_dataframe.groupby('identity'):
		dir_vec1 = np.array( [ df_couple['pos2X'] - df_couple['pos1X'] , \
						  	   df_couple['pos2Y'] - df_couple['pos1Y'] ] ).flatten()

		dir_vec2 = np.array( [ df_couple['pos1X'] - df_couple['pos2X'] , \
						  	   df_couple['pos1Y'] - df_couple['pos2Y'] ] ).flatten()

		f_vec1 = df_couple["force"].values[0]*dir_vec1 / np.linalg.norm(dir_vec1)
		f_vec2 = df_couple["force"].values[0]*dir_vec2 / np.linalg.norm(dir_vec2)

def calculate_force_components(args, temp_dataframe):
	"""Open input file, make a copy, remove unnecessary lines, process data,
	write to output file

	Returns: Pandas dataframe
	"""
	only_largest = args.largest

	# Define output dataframe

	output_df = pd.DataFrame(columns=['identity', 'cluster', \
									  'x1_force', 'y1_force', \
									  'x2_force', 'y2_force'] )

	largest_cluster_id = temp_dataframe['cluster'].mode().values[0]

	x1_force_sum = 0
	y1_force_sum = 0

	x2_force_sum = 0
	y2_force_sum = 0

	# iterate over cluster id and find x and y components of force vector
	for couple_id, df_couple in temp_dataframe.groupby('identity'):
		dir_vec1 = np.array( [ df_couple['pos2X'] - df_couple['pos1X'] , \
						  	   df_couple['pos2Y'] - df_couple['pos1Y'] ] ).flatten()

		dir_vec2 = np.array( [ df_couple['pos1X'] - df_couple['pos2X'] , \
						  	   df_couple['pos1Y'] - df_couple['pos2Y'] ] ).flatten()

		angle1 = np.arctan2(dir_vec1[1], dir_vec1[0])
		angle2 = np.arctan2(dir_vec2[1], dir_vec2[0])

		x1_force = np.cos(angle1)*df_couple['force'].values[0]
		y1_force = np.sin(angle1)*df_couple['force'].values[0]

		x2_force = np.cos(angle2)*df_couple['force'].values[0]
		y2_force = np.sin(angle2)*df_couple['force'].values[0]

		cluster_id = df_couple['cluster'].values[0]

		if only_largest:
			if cluster_id == largest_cluster_id:
				(output_df, x1_force_sum, y1_force_sum,  \
							x2_force_sum, y2_force_sum ) \
						  = write_to_dataframe(output_df, couple_id, cluster_id, \
											   x1_force, y1_force, \
											   x2_force, y2_force, \
											   x1_force_sum, y1_force_sum, \
											   x2_force_sum, y2_force_sum)
		else:
			(output_df, x1_force_sum, y1_force_sum,  \
						x2_force_sum, y2_force_sum ) \
					  = write_to_dataframe(output_df, couple_id, cluster_id, \
										   x1_force, y1_force, \
										   x2_force, y2_force, \
										   x1_force_sum, y1_force_sum, \
										   x2_force_sum, y2_force_sum)

	return output_df

def write_output_file(file_dict, output_df):
	# Write to output file
	output_file_path = Path(output_file_name)
	output_df.to_csv(output_file_path, float_format='%.3f', header=False, index=None, sep="\t")

def delete_temp_file(file_dict):
	try:
		os.remove(file_dict["temp"]["path"])
	except OSError as e:  ## if failed, report it back to the user ##
		print ("Error: %s - %s." % (e.filename, e.strerror))

def main(argv):

	# Get file name(s) from command line arguments
	args = get_args(argv)

	# Do the calculations and output results to file

	process_file(args)

if __name__ == "__main__":
	main(sys.argv[1:])
