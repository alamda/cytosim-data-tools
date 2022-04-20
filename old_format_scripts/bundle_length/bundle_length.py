#!/usr/bin/python
import sys # for command line arguments
import getopt # for option flags for command line arguments

# https://stackoverflow.com/a/42288083
from pathlib import Path # for stripping filename extensions

import os # for removing files

import pandas as pd # for processing data file

pd.set_option("display.max_rows", None, "display.max_columns", None)



# for calculating the distance matrix
from scipy.spatial.distance import squareform, pdist

import numpy as np
from numpy.polynomial import Polynomial

import matplotlib.pyplot as plt

from scipy.interpolate import UnivariateSpline

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


	#%  cluster nb_fibers  fiber_id      posX      posY      dirX      dirY
	# Drop columns with unnecessary data
	temp_dataframe = temp_dataframe.drop(["%"], axis=1)

	#temp_dataframe = temp_dataframe.rename(columns={"identity":"filID"})

	# Update the temp file, mostly for debugging.
	# File not used for calculations, calcs done with the dataframe object
	temp_dataframe.to_csv(temp_file_name, sep="\t", index=None)

	### Write to output file ###
	output_file_path = Path(output_file_name)

	### Perform bundle length calculations ###

	# split data frames into separate clusters

	output_df = pd.DataFrame(columns=['cluster_size', 'end_end_length'])


	for cluster, df_cluster in temp_dataframe.groupby('cluster'):
		# find end-to-end distance of bundle
		# (longest distance between points within cluster)

		# Distance matrix
		# https://stackoverflow.com/a/39205919
		# https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.iloc.html
		distance_matrix_dataframe = \
			pd.DataFrame(squareform(pdist(df_cluster.iloc[:, lambda df_cluster: [3,4]])), \
									columns=None,\
									index=None )

		# replace zero values with NaN
		df = distance_matrix_dataframe[distance_matrix_dataframe.gt(0)]

		# check that the minimum pair distance is less than 0.25 for a given filament
		df2 = df.min(axis=0)
		idx = df2[df2.lt(0.25)].index

		# get the max distances from the filaments which are within the cutoff
		# enforced above
		df3 = df.iloc[idx]
		max_pair_dist = df3.max().max()

		cluster_size = df_cluster.shape[0]


		# TODO: find arclength of bundle
		#
		# calculate curve along long axis of bundle and find its length

		# sum of distances for each filament in cluster that satisfies the min distance cutoff
		# normalized by number of pair distance each filament has
		# inverse of sum will be used as a weight factor when calculating splines
		# in short, filaments that are on average closer to their nehbors will be weighted more
		N_pairs = distance_matrix_dataframe[idx].shape[0] * (distance_matrix_dataframe[idx].shape[0] - 1)
		dist_sum = (distance_matrix_dataframe[idx].sum(axis=0)/N_pairs)
		inv_dist_sum_norm = (dist_sum-dist_sum.min())/(dist_sum.max()-dist_sum.min())


		spline_weights = inv_dist_sum_norm.values #np.sqrt(distance_matrix_dataframe[idx]**2).sum(axis=0)/N_pairs
		# print()


		pos_array = df_cluster.iloc[idx][['posX','posY']].values
		# pos_array = pos_array[pos_array[:,0].argsort()]

		if (pos_array.shape[0] > 5):
			# rotate pos_array to minimize variance in x values
			theta_arr = np.linspace(0, np.pi, 100, endpoint=True)

			new_pos_array = pos_array

			for theta in theta_arr:
				c, s = np.cos(theta), np.sin(theta)
				R = np.array(((c, -s), (s, c)))

				tmp_pos_array = np.zeros(pos_array.shape)

				for pos_idx in range(0, pos_array.shape[0]):
					tmp_pos_array[pos_idx] = R.dot(pos_array[pos_idx])

				if (np.var(tmp_pos_array[:,0]) < np.var(new_pos_array[:,0])):
					new_pos_array=tmp_pos_array


			# https://stackoverflow.com/a/52020098
			pos_array = new_pos_array[pos_array[:,1].argsort()]

			# print(pos_array)

			x = pos_array[:,0]
			y = pos_array[:,1]

			# Linear length along the line:
			distance = np.cumsum( np.sqrt(np.sum( np.diff(pos_array, axis=0)**2, axis=1 )) )
			distance = np.insert(distance, 0, 0)/distance[-1]

			spline_weights = np.zeros(pos_array.shape[0])

			for pos_idx in range(0, pos_array.shape[0]):
				shift = np.abs(pos_array[pos_idx,0] - np.mean(pos_array[:,0]))
				diff = shift - np.std(pos_array[:,0])
				if diff < 0 :
					spline_weights[pos_idx] =  np.abs(diff)

			# spline_weights = (spline_weights - spline_weights.min())/(spline_weights.max() - spline_weights.min())

			spline_weights = None
			# print(spline_weights)

			s_val = None

			# Build a list of the spline function, one for each dimension:
			splines1 = [UnivariateSpline(distance, coords, k=1, w=spline_weights, s=s_val) for coords in pos_array.T]
			splines2 = [UnivariateSpline(distance, coords, k=2, w=spline_weights, s=s_val) for coords in pos_array.T]
			splines3 = [UnivariateSpline(distance, coords, k=3, w=spline_weights, s=s_val) for coords in pos_array.T]
			splines4 = [UnivariateSpline(distance, coords, k=4, w=spline_weights, s=s_val) for coords in pos_array.T]
			splines5 = [UnivariateSpline(distance, coords, k=5, w=spline_weights, s=s_val) for coords in pos_array.T]

			print([spl.get_residual() for spl in splines2])
			print([spl.get_residual() for spl in splines3])
			print([spl.get_residual() for spl in splines4])
			print([spl.get_residual() for spl in splines5])

			# Computed the spline for the asked distances:
			alpha = np.linspace(0,1, 100)
			points_fitted2 = np.vstack([ spl(alpha) for spl in splines2 ] ).T
			points_fitted3 = np.vstack([ spl(alpha) for spl in splines3 ] ).T
			points_fitted4 = np.vstack([ spl(alpha) for spl in splines4 ] ).T
			points_fitted5 = np.vstack([ spl(alpha) for spl in splines5 ] ).T

			# Graph:
			# plt.plot(*pos_array.T, 'ok', label='original points');
			# plt.plot(*points_fitted1.T, '-', label='fitted spline k=1, s=None');

			# plt.plot(*points_fitted2.T, '-', lw=2, label='fitted spline k=2, s=None');
			# plt.plot(*points_fitted3.T, '-', lw=2, label='fitted spline k=3, s=None');
			# plt.plot(*points_fitted4.T, '-', lw=2, label='fitted spline k=4, s=None');
			# plt.plot(*points_fitted5.T, '-', lw=2, label='fitted spline k=5, s=None');
			# plt.axis('equal'); plt.legend(); plt.xlabel('x'); plt.ylabel('y');
			# plt.show()

			arc_length = np.sum(np.sqrt(np.sum( np.diff(points_fitted5, axis=0)**2, axis=1 )))

			# add values to data frame which will be written to the output file
			output_df = output_df.append({'cluster_size' : int(cluster_size), \
										  'end_end_length' : max_pair_dist, \
										  'arc_length' : arc_length },\
										 ignore_index=True)



	output_df.to_csv(output_file_path.with_suffix('.len.dat'), header=True, index=None, sep="\t")

	### OLD CODE BELOW ###

	### Perform calculations ###

	# Distance matrix
	# https://stackoverflow.com/a/39205919
	# https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.iloc.html
	#distance_matrix_dataframe = \
	#	pd.DataFrame(squareform(pdist(temp_dataframe.iloc[:, lambda temp_dataframe: [1,2]])), \
	#							columns=None, #temp_dataframe.filID.unique(), \
	#							index=None ) #temp_dataframe.filID.unique())

	# Angle matrix
	# scipy's pdist with cosine metric calculates the cosine distance bw vectors:
	# 1 - dot_prod = 1 - cos(angle)
	# Subtract the cosine distance from 1 to get the cosine similarity,
	# aka the cosine of the angle between the vectors
	# https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.pdist.html
	#angle_matrix_dataframe = \
	#	pd.DataFrame(1-squareform(pdist(temp_dataframe.iloc[:, lambda temp_dataframe: [3,4]], 'cosine')), \
	#							columns=None, \
	#							index=None)

	# Take the arccos of all values in the dataframe to calculate angles
	#angle_matrix_dataframe = angle_matrix_dataframe.apply(np.arccos)



	#distance_matrix_dataframe.to_csv(output_file_path.with_suffix('.dist.dat'), header=False, index=None, sep="\t")
	#angle_matrix_dataframe.to_csv(output_file_path.with_suffix('.ang.dat'), header=False, index=None, sep="\t")

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
