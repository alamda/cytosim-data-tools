import numpy as np
import os
import argparse

import sys
sys.path.insert(1, '/home/yuqingqiu/erik-emus/EMUS/src')
from emus import usutils as uu
from emus import emus, avar

import matplotlib.pyplot as plt

class CloningData:
	# For data from data files for all clones of all iterations
	# Multiple values of alpha
	def __init__(self):
		# Get command line arguments when running the script
		args = self.init_parser()

		self.k_B = 1.0

		# Temperature =
		self.kT = 1/args.beta

		self.T = args.temp

		# Cloning iteration length
		self.tau = args.tau
		# Inverse temperature
		# self.beta = args.beta

		# Bin size
		self.bin_size = args.binsize

		# Meta file name
		self.meta_file_name = args.metafile

		# Dimension of CV
		self.dim = args.dim

		# number of bins
		self.num_bins = args.nbins

		self.period = None
		self.neighbors = None

	def init_parser(self):
		parser = argparse.ArgumentParser(description='Process data files with avg wDot values over iterations')
		# Inverse temperature
		parser.add_argument('--beta', type=float, default=1.0)
		# Cloning interation length
		parser.add_argument('--tau', type=float, required=True)
		# Bin size for histogram
		parser.add_argument('--binsize', type=float, default=0.1)
		# Name of metafile with input data locations
		parser.add_argument('--metafile', type=str, required=True)
		# Dimension of CV space
		parser.add_argument('--dim', type=int, default=1)
		# Number of bins
		parser.add_argument('--nbins', type=int, default=30)
		# Temperature
		parser.add_argument('--temp', type=float, default=1.0)

		return parser.parse_args()

	def run_EMUS(self):
		# Load data
		psis, cv_trajs, neighbors = uu.data_from_meta(self.meta_file_name, self.dim, T=self.T, k_B=self.k_B, period=None)

		# Calculate the partition function for each window
		z, F = emus.calculate_zs(psis, neighbors=neighbors)

		# Calculate error in each z value from the first iteration.
		zerr, zcontribs, ztaus = avar.calc_partition_functions(psis, z, F, iat_method='acor')

		# Calculate the PMF from EMUS
		domain = ((-0.5, 6))           # Range of dihedral angle values
		pmf, edges = emus.calculate_pmf(cv_trajs, psis, domain, z, nbins=self.num_bins, kT=self.kT, use_iter=False)   # Calculate the pmf

		# Calculate z using the MBAR iteration.
		z_iter_1, F_iter_1 = emus.calculate_zs(psis, n_iter=1)
		z_iter_2, F_iter_2 = emus.calculate_zs(psis, n_iter=2)
		z_iter_5, F_iter_5 = emus.calculate_zs(psis, n_iter=5)
		z_iter_1k, F_iter_1k = emus.calculate_zs(psis, n_iter=1000)

		# Calculate new PMF
		iterpmf, edges = emus.calculate_pmf(cv_trajs, psis, domain, nbins=self.num_bins, z=z_iter_1k, kT=self.kT)
		# Get the asymptotic error of each histogram bin.
		pmf_av_mns, pmf_avars = avar.calc_pmf(cv_trajs, psis, domain, z, F, nbins=self.num_bins, kT=self.kT, iat_method=np.average(ztaus, axis=0))

		### Data Output Section ###

		# Plot the EMUS, Iterative EMUS pmfs.
		pmf_centers = (edges[0][1:]+edges[0][:-1])/2.

		self.x = pmf_centers
		self.y  = pmf_av_mns/self.tau
		self.err =1/self.tau*np.sqrt(pmf_avars)

		self.y_iter  = iterpmf/self.tau

myCloningData = CloningData()
myCloningData.run_EMUS()

# Combine prob distribution into a single 2d np.array to write to file

EMUS_rate_func_data_array = np.column_stack((myCloningData.x, myCloningData.y, myCloningData.err))
EMUS_rate_func_iter_data_array = np.column_stack((myCloningData.x, myCloningData.y_iter))

# Generate output file name
rate_func_output_file_name = "rate_func_EMUS.dat"
rate_func_iter_output_file_name = "rate_func_EMUS_iter.dat"

# Save data to file
np.savetxt(rate_func_output_file_name, EMUS_rate_func_data_array, delimiter="\t", fmt='%.8f')
np.savetxt(rate_func_iter_output_file_name, EMUS_rate_func_iter_data_array, delimiter="\t", fmt='%.8f')
