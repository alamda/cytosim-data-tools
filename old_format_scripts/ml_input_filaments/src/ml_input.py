#!/usr/bin/python

import sys # for command line arguments
import getopt # for option flags for command line arguments

# https://stackoverflow.com/a/42288083
from pathlib import Path # for stripping filename extensions

import os # for removing files

import pandas as pd # for processing data file

# for calculating the distance matrix
from scipy.spatial.distance import squareform, pdist

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
				temp_file.write(line)

	# Delete columns with extraneous data
	# Read the copy fixed width file that is output by Cytosim
	temp_dataframe = pd.read_fwf(temp_file_name)

	# Drop columns with unnecessary data
	temp_dataframe = temp_dataframe.drop(["%", "class", "length", "cosinus", \
										  "organizer", "endToEnd"], axis=1)

	temp_dataframe = temp_dataframe.rename(columns={"identity":"filID"})

	# Update the temp file, mostly for debugging.
	# File not used for calculations, calcs done with the dataframe object
	temp_dataframe.to_csv(temp_file_name, sep="\t", index=None)

	### Perform calculations ###

	# Distance matrix
	# https://stackoverflow.com/a/39205919
	# https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.iloc.html
	distance_matrix_dataframe = \
		pd.DataFrame(squareform(pdist(temp_dataframe.iloc[:, lambda temp_dataframe: [1,2]])), \
								columns=None, #temp_dataframe.filID.unique(), \
								index=None ) #temp_dataframe.filID.unique())

	# Angle matrix
	# scipy's pdist with cosine metric calculates the cosine distance bw vectors:
	# 1 - dot_prod = 1 - cos(angle)
	# Subtract the cosine distance from 1 to get the cosine similarity,
	# aka the cosine of the angle between the vectors
	# https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.pdist.html
	angle_matrix_dataframe = \
		pd.DataFrame(1-squareform(pdist(temp_dataframe.iloc[:, lambda temp_dataframe: [3,4]], 'cosine')), \
								columns=None, \
								index=None)

	# Take the arccos of all values in the dataframe to calculate angles
	angle_matrix_dataframe = angle_matrix_dataframe.apply(np.arccos)

	### Write to output file ###
	output_file_path = Path(output_file_name)

	distance_matrix_dataframe.to_csv(output_file_path.with_suffix('.dist.dat'), header=False, index=None, sep="\t")
	angle_matrix_dataframe.to_csv(output_file_path.with_suffix('.ang.dat'), header=False, index=None, sep="\t")

	### Delete the temporary file after writing to output ###
	# https://stackoverflow.com/a/42641792
	try:
		os.remove(temp_file_path)
	except OSError as e:  ## if failed, report it back to the user ##
		print ("Error: %s - %s." % (e.filename, e.strerror))

def main(argv):

	# Get file name(s) from command line arguments
	(input_file_name, output_file_name) = get_file_names(argv)

	# Do the pairwise calculations (distances and angles)
	process_file(input_file_name, output_file_name)

if __name__ == "__main__":
	main(sys.argv[1:])
