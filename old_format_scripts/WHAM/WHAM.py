import numpy as np
import os
import argparse

import matplotlib.pyplot as plt

"""
Author: Alexandra Lamtyugina
Date: 24 March 2021

Usage: python WHAM.py --tau TAU [--beta BETA]
--tau: iteration length for cloning simulations
--beta: inverse temperature (default value 1)

Data files for different values of alpha should have the following naming scheme:
<alpha>-*.txt
<alpha> is the numeric value of alpha, followed by a '-'

This script generates an output file "prob_dist_tau<TAU>.dat"
"""

class CloningData:
	# For data from data files for all clones of all iterations
	# Multiple values of alpha
	def __init__(self):
		# Get command line arguments when running the script
		args = self.init_parser()

		# Cloning iteration length
		self.tau = args.tau
		# Inverse temperature
		# self.beta = args.beta

		# Bin size
		self.bin_size = args.binsize

		# Dictionary: {alpha: np.array([iteration #, avg wDot for clone])}
		# Read from file
		self.wDot_avg_dict = self.get_wDot_data()

		# Histogram values and bin centers of all of the wDot values read from file by self.get_wDot_data()
		self.wDot_avg_hist, self.wDot_avg_bin_centers = self.calculate_wDot_hist()

		# Dictionary: {alpha: num_samples}
		self.num_samples_dict = self.calculate_num_samples()

		# Dictionary: {alpha: norm_factor}
		# Initialize all values to 1, and the interatively recalculate
		self.norm_factor_dict = dict.fromkeys(self.wDot_avg_dict.keys(),1)

		# Dictionary: {alpha: np.array([bias factor over wDot range defined by self.wDot_avg_bin_centers])}
		self.bias_factor_dict = self.calculate_bias_factors()

	def init_parser(self):
		parser = argparse.ArgumentParser(description='Process data files with avg wDot values over iterations')
		# Inverse temperature
		parser.add_argument('--beta', type=float, default=1.0)
		# Cloning interation length
		parser.add_argument('--tau', type=float, required=True)
		# Bin size for histogram
		parser.add_argument('--binsize', type=float, default=0.1)

		return parser.parse_args()

	def get_wDot_data(self):
		# Initialize empty data dictionary
		data = {}

		# Iterate over files in current directory
		with os.scandir(os.getcwd()) as entries:
			for entry in entries:
				# If file ends in .txt
				if entry.is_file() and ".txt" in entry.name:
					# Alpha is the first value before '-'
					alpha = float(entry.name.split('-')[0].replace('n','-'))


					# Open file
					with open (entry, 'r') as file:
						# Load data from file into np array
						# https://stackoverflow.com/a/6583635
						wDots_avg_array = np.array([[float(x) for x in line.split()] for line in file])

					# Save np.array with wDot data to dictionary
					data[alpha] = wDots_avg_array

		return data

	def calculate_wDot_hist(self):
		# Initialize empty list with all avg wDot values for all alphas
		wDot_combined = []


		# Iterate over keys (alphas) and values (wDot averages)
		for alpha, wDot_avg_raw_data in self.wDot_avg_dict.items():
			# Only need wDot avg values, [:,0] are the iteration numbers (not used)
			# Conversion to list needed for cases where different alphas have
			# different numbers of avg wDot data points
			wDot_combined += wDot_avg_raw_data[:,1].tolist()

		# Calculate the histogram from all wDot avg values for all alphas
		# bins='auto' calculate the number of bins using Friedman-Diaconis or Sturges rule,
		# whichever returns the larger number of bins

		# Automatically calculate the number of bins using Friedman-Diacons or Sturgis rule,
		# whichever returns the larger number of bins
		#wDot_avg_hist, wDot_avg_bin_edges = np.histogram(np.array(wDot_combined).flatten(), bins='auto')


		data = np.array(wDot_combined).flatten()

		# Custom bin size
		bin_width=self.bin_size
		bin_arr=np.arange(min(data), max(data) + bin_width, bin_width)

		combined_hist, combined_bin_edges = \
			np.histogram(data, bins=bin_arr)

		combined_hist = np.zeros(combined_hist.shape)

		combined_bin_centers = combined_bin_edges[:-1] + np.diff(combined_bin_edges)/2

		for alpha, wDot_avg_raw_data in self.wDot_avg_dict.items():
			tmp_data = wDot_avg_raw_data[:,1]
			tmp_hist, tmp_edges = \
				np.histogram(tmp_data, bins=bin_arr) #\
				# + alpha * combined_bin_centers[:]

			#unbias_factor_arr = np.array([np.exp(-alpha*x*self.tau) for x in combined_bin_centers ])

			#tmp_hist = tmp_hist*unbias_factor_arr

			combined_hist += tmp_hist

		# Calculate the center of each bin (to use in plotting)


		return (combined_hist, combined_bin_centers)

	def calculate_num_samples(self):
		# Create empty dictionary for number of samples with same keys (alphas)
		# as those read in from data files
		num_samples_dict = dict.fromkeys(self.wDot_avg_dict.keys(),[])

		# Iterate over keys (alphas)
		for alpha in num_samples_dict:
			# Count the number of wDot avg values
			num_samples_dict[alpha] = self.wDot_avg_dict[alpha].shape[0]

		return num_samples_dict

	def calculate_bias_factors(self):
		# Create empty dictionary for bias factors with same keys (alphas)
		# as those read in from data files
		bias_factor_dict = dict.fromkeys(self.wDot_avg_dict.keys(),[])

		# Iterate over keys (alphas)
		for alpha in bias_factor_dict:
			# Calculate the bias factor array for each alpha
			# self.wDot_avg_bin_centers is a np.array, making bias_factor_dict[alpha] values np.array as well
			bias_factor_dict[alpha] = np.exp(alpha * self.wDot_avg_bin_centers * self.tau)

		return bias_factor_dict

	def calculate_prob_dist(self):
		# Create a 0-filled np.array over wDot range
		denominator = np.zeros(self.wDot_avg_bin_centers.shape)

		# Iterate over keys (alphas)
		for alpha in self.wDot_avg_dict:
			# Add to the denominator np.array
			# The bias factor dictionary entry is an array, the rest are scalar values
			denominator = np.add(denominator, \
								 # ^ np.array
								 self.num_samples_dict[alpha] * \
								 # ^ int
									self.norm_factor_dict[alpha] * \
									# ^ float
									self.bias_factor_dict[alpha] \
									# ^ np.array
								)

		# Divide histogram of avg wDot by calculated denominator (np.array divided by np.array)

		p_dist = self.wDot_avg_hist / denominator
		p_dist = self.normalize_p_dist(p_dist)

		p_dist = p_dist.astype('float')

		return p_dist



	def calculate_norm_factors(self):
		# Iterate over keys (alphas)
		for alpha in self.norm_factor_dict:
			# Normalize sum over wDot range of P_0(<wDot>) * exp(-beta*alpha*tau*<wDot>)
			self.norm_factor_dict[alpha] = 1 / (np.sum(np.multiply(self.prob_dist, self.bias_factor_dict[alpha])))

	def normalize_p_dist(self, p_dist):
		# Assuming each bin is the same size (bold assumption, but it works here)
		bin_width = self.wDot_avg_bin_centers[1] - \
					self.wDot_avg_bin_centers[0]

		# Calculate the integral of the prob dist using the rectangular approximation
		integral = np.sum(np.array([i*bin_width for i in p_dist]))

		# Normalize the probability distribution
		p_dist /= integral

		return(p_dist)

	def iterate_WHAM(self, n_iters):
		# Iteratively solve for norm factors
		for i in range (0,n_iters):
			self.prob_dist = self.calculate_prob_dist()
			self.calculate_norm_factors()

		p_dist = np.array([ np.nan if x < 1e-8 else x for x in self.prob_dist])

		rate_func = -np.log(p_dist) /self.tau

		min_val = float(np.nanmin(rate_func, axis=0))


		rate_func -=  min_val

		self.rate_func = rate_func

	def monitor_convergence(self):
		# TODO: write a function that monitors the convergence of norm factors
		# Currently just iterating 100 times
		pass

# Generate instance of CloningData class
myCloningData = CloningData()

myCloningData.iterate_WHAM(1000)

# Combine prob distribution into a single 2d np.array to write to file
WHAM_p_dist_data_array = np.column_stack((myCloningData.wDot_avg_bin_centers, myCloningData.prob_dist))

WHAM_rate_func_data_array = np.column_stack((myCloningData.wDot_avg_bin_centers, myCloningData.rate_func))

# Generate output file name
p_dist_output_file_name = "prob_dist.dat"
rate_func_output_file_name = "rate_func.dat"

# Save data to file
np.savetxt(p_dist_output_file_name, WHAM_p_dist_data_array, delimiter="\t", fmt='%.8f')
np.savetxt(rate_func_output_file_name, WHAM_rate_func_data_array, delimiter="\t", fmt='%.8f')
