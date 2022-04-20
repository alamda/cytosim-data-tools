#!/usr/bin/python
"""Usage:
python /path/to/force-on-single.py -i single_force.txt

The single_force.txt file is generated using a custom Cytosim report function:
report2 single:force

i.e.:

singularity exec /path/to/cytosim_sandbox.sif /home/cytosim/bin/report2 single:force frame=1000 > single_force.txt

Make sure the report is generated for the last frame only (not for all frames)

Output file name is automatically generated as <input file basename>.dat
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
	# https://stackoverflow.com/a/31347222
	parser.add_argument('--xdir', '-x', action='store_true', help='calculate sum of forces in x direction')
	parser.add_argument('--ydir', '-y', action='store_true', help='calculate sum of forces in y direction')

	args = parser.parse_args()

	return args

def process_file(args):
	"""Open input file, make a copy, remove unnecessary lines, process data,
	write to output file
	"""
	input_file_name=args.ifile
	output_file_name=args.ofile

	xdir_toggle = args.xdir
	ydir_toggle = args.ydir

	# If outputfile name not provided, replace/add suffix '.dat' to input file name
	if not output_file_name:
		input_file_path = Path(input_file_name)
		if (xdir_toggle and ydir_toggle) :
			output_file_name = input_file_path.with_suffix('.xy.dat')
		elif xdir_toggle:
			output_file_name = input_file_path.with_suffix('.x.dat')
		elif ydir_toggle:
			output_file_name = input_file_path.with_suffix('.y.dat')

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

	# Update the temp file, mostly for debugging.
	# File not used for calculations, calcs done with the dataframe object
	temp_dataframe.to_csv(temp_file_name, sep="\t", index=None)

	output_df = pd.DataFrame(columns=['class'])

	# Define output dataframe
	if xdir_toggle:
		output_df['sum_fx'] = np.nan
	if ydir_toggle:
		output_df['sum_fy'] = np.nan

	# iterate over filament id and sum tensions
	for single_class, df_single_class in temp_dataframe.groupby('class'):
		new_df = pd.DataFrame([single_class], columns=['class'])
		if xdir_toggle:
			sum_fx=df_single_class['forceX'].sum()
			new_df['sum_fx'] = sum_fx
		if ydir_toggle:
			sum_fy=df_single_class['forceY'].sum()
			new_df['sum_fy'] = sum_fy

		output_df =pd.concat([output_df, new_df], ignore_index=False)

	# Write to output file
	output_file_path = Path(output_file_name)
	output_df.to_csv(output_file_path, float_format='%.3f', header=False, index=None, sep="\t")

	try:
		os.remove(temp_file_path)
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
