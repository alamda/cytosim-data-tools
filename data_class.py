import sys # for command line arguments
import argparse # for parsing command line arguments to script

# https://stackoverflow.com/a/42288083
from pathlib import Path # for stripping filename extensions

import os # for removing files

import pandas as pd # for processing data file

# pd.set_option("display.max_rows", None, "display.max_columns", None)

import pytest

class RuntimeArgumentError(ValueError):
	pass

class MultiFrameError(ValueError):
	pass

class Data():
	def __init__(self, argv=sys.argv[1:], column_list=['class', 'identity']):

		# if (	('--ifile' not in argv) or \
		#  		('-i' not in argv)) or \
		# 		(len(argv) < 2):
		# 	raise ValueError("No input file specified")

		if argv != sys.argv[1:]:
			os.chdir(sys.path[0])

		self.args = self.get_args(argv)
		self.file_dict = self.get_file_paths()

		self.temp_dataframe = pd.DataFrame()
		self.preprocess_file()

		self.column_list = column_list
		self.get_relevant_columns(self.column_list)

		self.output_df = pd.DataFrame()

	def __del__(self):
		self.delete_temp_file()

	def get_args(self, argv):
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

	def get_file_paths(self):
		"""Generate the paths for the file names provided by args

		Return: file names + paths? as a dict?
		"""
		input_file_name=self.args.ifile
		output_file_name=self.args.ofile

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

	def preprocess_file(self):
		"""Pre-process input data to remove extraneous (non-data or non-column
		header) lines.

		Returns: Pandas dataframe
		"""

		# Remove blank lines and lines with % (Cytosim comments)
		# BUT Keep line with column headers
		# https://stackoverflow.com/a/11969474 , https://stackoverflow.com/a/2369538
		with open(self.file_dict["input"]["path"]) as input_file, \
			 open(self.file_dict["temp"]["path"], 'w') as temp_file:
			for line in input_file:
				if not (line.isspace() or ("%" in line and (not "identity" in line))):
					temp_file.write(line.replace("%",""))

		# Read the whitespace-delimited data file that is output by Cytosim
		self.temp_dataframe = pd.read_csv(self.file_dict["temp"]["path"], delim_whitespace=True)

		# Check that data from only one simulation frame was loaded
		if self.temp_dataframe["identity"].isin(["identity"]).any():
			raise ValueError("Data for more than one frame loaded.")

		self.write_temp_dataframe()

	def get_relevant_columns(self, column_list):
		self.temp_dataframe = self.temp_dataframe[column_list]
		self.write_temp_dataframe()

	def write_temp_dataframe(self):
		# Update the temp file, mostly for debugging.
		# File not used for calculations, calcs done with the dataframe object
		self.temp_dataframe.to_csv(self.file_dict["temp"]["path"], sep="\t", index=None)

	def write_output_file(self):
		# Write to output file
		self.output_df.to_csv(self.file_dict["output"]["path"], float_format='%.3f', header=True, index=None, sep="\t")

	def delete_temp_file(self):
		try:
			os.remove(self.file_dict["temp"]["path"])
		except OSError as e:  ## if failed, report it back to the user ##
			print ("Error: %s - %s." % (e.filename, e.strerror))
