import argparse

import sys # for command line arguments
import getopt # for option flags for command line arguments

# https://stackoverflow.com/a/42288083
from pathlib import Path # for stripping filename extensions

import os # for removing files
import pandas as pd # for processing data file

def init_parser():
	parser = argparse.ArgumentParser(description='Convert Cytosim output file into Pandas dataframe')
	# Input file name
	parser.add_argument('-i', '--input', type=str, required=True, help="input file name (required)")
	# Output file name
	parser.add_argument('-o', '--output', type=str, default='', help="output file name (optional, default use input file root name with new extension '.dat')")

	return parser.parse_args()

def import_file_as_pd():
	"""Parse the command line input flags and arguments
	Open input file, convert data to pandas dataframe, generate output file path
	"""
	args = init_parser()

	input_file_name = args.input
	output_file_name = args.output

	# If outputfile name not provided, replace/add suffix '.dat' to input file name
	if not output_file_name:
		input_file_path = Path(input_file_name)

		ext = os.path.splitext(input_file_path)[-1].lower()

		# Check that the input file does not have *.dat extension to avoid overwriting
		if ext != '.dat':
			output_file_name = input_file_path.with_suffix('.dat')
		else:
			output_file_name = input_file_path.with_suffix('.dat.dat')

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
				temp_file.write(line)

	# Remove blank lines and lines with % (Cytosim comments)
	# BUT Keep line with column headers (includes posX string)
	# https://stackoverflow.com/a/11969474 , https://stackoverflow.com/a/2369538
	with open(input_file_name) as input_file, open(temp_file_name, 'w') as temp_file:
		for line in input_file:
			if not (line.isspace() or ("%" in line and (not "posX" in line))):
				temp_file.write(line)

	# Read the copy fixed width file that is output by Cytosim
	temp_dataframe = pd.read_fwf(temp_file_name)

	# Remove the leading '%' column (Cytosim comment, no data in that column)
	temp_dataframe = temp_dataframe.drop(["%"], axis=1)

	# Generate the path for the output file
	output_file_path = Path(output_file_name)

	return (temp_dataframe, input_file_path, output_file_path)

print(import_file_as_pd())
