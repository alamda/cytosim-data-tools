from data_class import Data, RuntimeArgumentError, MultiFrameError
import argparse
from pathlib import Path, PosixPath
import pandas as pd
import os
import numpy as np
import sys
import pytest
import contextlib

# def test_init_sys_args():
# 	with pytest.raises(ValueError) as exp:
# 		myData = Data()
#
# 	assert str(exp.value) == "No input file specified"

# @contextlib.contextmanager
# def test_dir(younger):
# 	older = os.pwd()
# 	try:
# 		os.chdir(older)
# 		yield
# 	finally:
# 		os.chdir(older)

# with test_dir("/"):
# 	os.system("rm -rf *")

def test_init():
	myData = Data(argv=['--ifile', 'link_cluster.txt', \
						'--ofile', 'link_cluster.out.txt', \
						'--largest'])

def test_get_args():
	os.chdir(sys.path[0])

	myData = Data(argv=['--ifile', 'link_cluster.txt', \
						'--ofile', 'link_cluster.out.txt', \
						'--largest'])


	assert type(myData.args.ifile) == str
	assert len(myData.args.ifile) > 0

	assert type(myData.args.ofile) == str
	assert type(myData.args.largest) == bool

def test_get_file_paths():
	myData = Data(argv=['--ifile', 'link_cluster.txt', \
						'--ofile', 'link_cluster.out.txt', \
						'--largest'])

	for file_type in myData.file_dict:
		assert type(myData.file_dict[file_type]["name"]) == str
		assert type(myData.file_dict[file_type]["path"]) == PosixPath

def test_preprocess_file_multiple_frames():
	with pytest.raises(ValueError) as exp:
		os.chdir(sys.path[0])

		myData = Data(argv=['--ifile', 'link_cluster_two_frames.txt', \
							'--largest'])

	assert str(exp.value) == "Data for more than one frame loaded."

# def test_write_output_file():
# 	pass
#
# def test_delete_temp_file():
# 	pass
