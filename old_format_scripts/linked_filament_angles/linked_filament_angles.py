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
                        if not (line.isspace() or ("%" in line and (not "pos1X" in line))):
                                temp_file.write(line.replace("%    ",""))

        # Delete columns with extraneous data
        # Read the copy fixed width file that is output by Cytosim
        temp_dataframe = pd.read_csv(temp_file_name, delim_whitespace=True)


        #%  cluster nb_fibers  fiber_id      posX      posY      dirX      dirY
        # Drop columns with unnecessary data
        #temp_dataframe = temp_dataframe.drop(["%"], axis=1)

        #temp_dataframe = temp_dataframe.rename(columns={"identity":"filID"})

        # Update the temp file, mostly for debugging.
        # File not used for calculations, calcs done with the dataframe object
        temp_dataframe.to_csv(temp_file_name, sep="\t", index=None)

        ### Write to output file ###
        output_file_path = Path(output_file_name)

        ### Perform bundle length calculations ###

        # split data frames into separate clusters

        output_df = pd.DataFrame(columns=['angle'])


        output_df['angle'] = np.arccos(temp_dataframe.cos_angle)
        output_df['sin_angle'] = np.sin(output_df['angle'])

        # add values to data frame which will be written to the output file
        #output_df = output_df.append({'angle' : np.arccos(temp_dataframe['cos_angle'])}, \
        #                              ignore_index=True)



        output_df['angle'].to_csv(output_file_path.with_suffix('.angles.dat'), header=False, index=None, sep="\t")

        output_df['sin_angle'].to_csv(output_file_path.with_suffix('.sin_angle.dat'), header=False, index=None, sep="\t")


        ### Delete the temporary file after writing to output ###
        # https://stackoverflow.com/a/42641792
        try:
                os.remove(temp_file_path)
        except OSError as e:  ## if failed, report it back to the user ##
                print ("Error: %s - %s." % (e.filename, e.strerror))

        ### Calculate the histogram of the angles ###
        #bin_size=0.1
        #bin_arr = np.arange(output_df.angle.min(), output_df.angle.max(), bin_size)
        #hist, bin_edges = np.histogram(output_df.angle, bins=bin_arr)

        #bin_centers = (bin_edges[1:] + bin_edges[:-1])/2.0

        #np.savetxt('angles_hist.dat', np.column_stack((bin_centers,hist)))

def main(argv):

        # Get file name(s) from command line arguments
        (input_file_name, output_file_name) = get_file_names(argv)

        # Do the pairwise calculations (distances and angles)
        process_file(input_file_name, output_file_name)

if __name__ == "__main__":
        main(sys.argv[1:])
