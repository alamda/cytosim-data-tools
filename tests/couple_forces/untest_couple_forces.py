import pytest

import argparse
from pathlib import Path, PosixPath
import pandas as pd
import os
import numpy as np
import sys

from couple_forces.couple_forces \
	import get_args, get_file_paths, preprocess_file, \
		   calculate_force_components, write_to_dataframe, calc_force_vec

def test_get_args():
	args = get_args(['--ifile', 'input_filename', \
					 '--ofile', 'output_filename', \
					 '--largest'])

	assert type(args.ifile) == str
	assert type(args.ofile) == str
	assert type(args.largest) == bool

def test_get_file_paths():
	args = get_args(['--ifile', 'my_input', \
					 '--ofile', 'my_output', \
					 '--largest'])

	file_dict = get_file_paths(args)

	for file_type in file_dict:
		assert type(file_dict[file_type]["name"]) == str
		assert type(file_dict[file_type]["path"]) == PosixPath

def test_preprocess_file_multiple_frames():
	with pytest.raises(ValueError) as exp:
		os.chdir(sys.path[0])

		args = get_args(['--ifile', 'link_cluster_two_frames.txt', \
						 '--largest'])

		file_dict = get_file_paths(args)
		temp_dataframe = preprocess_file(file_dict)

	assert str(exp.value) == "Data for more than one frame loaded."

def test_write_to_dataframe():
	os.chdir(sys.path[0])

	args = get_args(['--ifile', 'link_cluster_test_data.txt', \
					 '--largest'])

	file_dict = get_file_paths(args)
	temp_dataframe = preprocess_file(file_dict)

	output_df = pd.DataFrame(columns=['identity', 'cluster', \
									  'x1_force', 'y1_force', \
									  'x2_force', 'y2_force'] )

	(output_df, x1_force_sum, y1_force_sum,  \
				x2_force_sum, y2_force_sum ) \
			  = write_to_dataframe(output_df, couple_id=10, cluster_id=3, \
								   x1_force=0.2, y1_force=0.1, \
								   x2_force=-0.3, y2_force=0.01, \
								   x1_force_sum=1.02, y1_force_sum=-0.86, \
								   x2_force_sum=-0.12, y2_force_sum=-0.23)

	assert round(x1_force_sum, 2) == 1.22
	assert round(y1_force_sum, 2) == -0.76
	assert round(x2_force_sum, 2) == -0.42
	assert round(y2_force_sum, 2) == -0.22

	(output_df, x1_force_sum, y1_force_sum,  \
				x2_force_sum, y2_force_sum ) \
			  = write_to_dataframe(output_df, couple_id=2, cluster_id=1, \
								   x1_force=-1.0, y1_force=2.5, \
								   x2_force=0.2, y2_force=-0.05, \
								   x1_force_sum=1.22, y1_force_sum=-0.76, \
								   x2_force_sum=-0.42, y2_force_sum=-0.22)

	assert round(x1_force_sum, 2) == 0.22
	assert round(y1_force_sum, 2) == 1.74
	assert round(x2_force_sum, 2) == -0.22
	assert round(y2_force_sum, 2) == -0.27

	assert output_df.loc[0].identity == 10
	assert output_df.loc[0].cluster  == 3
	assert output_df.loc[0].x1_force == 0.2
	assert output_df.loc[0].y1_force == 0.1
	assert output_df.loc[0].x2_force == -0.3
	assert output_df.loc[0].y2_force == 0.01

	assert output_df.loc[1].identity == 2
	assert output_df.loc[1].cluster  == 1
	assert output_df.loc[1].x1_force == -1.0
	assert output_df.loc[1].y1_force == 2.5
	assert output_df.loc[1].x2_force == 0.2
	assert output_df.loc[1].y2_force == -0.05

def test_calc_force_vec():
	os.chdir(sys.path[0])

	args = get_args(['--ifile', 'link_cluster_test_data.txt', \
					 '--largest'])

	file_dict = get_file_paths(args)
	temp_dataframe = preprocess_file(file_dict)

	calc_force_vec(args, temp_dataframe)


def test_calculate_force_components():
	os.chdir(sys.path[0])

	args = get_args(['--ifile', 'link_cluster_test_data.txt', \
					 '--largest'])

	file_dict = get_file_paths(args)
	temp_dataframe = preprocess_file(file_dict)

	output_df = calculate_force_components(args, temp_dataframe)


def test_write_output_file():
	pass

def test_delete_temp_file():
	pass
