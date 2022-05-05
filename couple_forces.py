from data_class import Data

import numpy as np
import pandas as pd

class CoupleForces(Data):
	def __init__(self, column_list):
		super().__init__(column_list=column_list)

		self.sum_output_df = pd.DataFrame()

	def write_to_dataframe(self, couple_id, cluster_id, \
						   x1_force, y1_force, x2_force, y2_force, \
						   x1_force_sum, y1_force_sum, x2_force_sum, y2_force_sum):

		new_df1 = pd.DataFrame([[ couple_id, cluster_id, \
								  x1_force, y1_force ]],\
								  columns=[ 'id', 'c',\
											'fx1', 'fy1' ])

		new_df2 = pd.DataFrame([[ couple_id, cluster_id, \
								  x2_force, y2_force ]],\
								  columns=[ 'id', 'c', \
											'fx2', 'fy2' ])

		new_df_both = new_df1.merge(new_df2, on=['id','c'])

		self.output_df = pd.concat([self.output_df, new_df_both], ignore_index=True)

		x1_force_sum += x1_force
		y1_force_sum += y1_force

		x2_force_sum += x2_force
		y2_force_sum += y2_force

		return ( x1_force_sum, y1_force_sum, x2_force_sum, y2_force_sum )

	def calc_force_vec(self):

		x1_force_sum = 0
		y1_force_sum = 0

		x2_force_sum = 0
		y2_force_sum = 0

		for couple_id, df_couple in self.temp_dataframe.groupby('identity'):
			dir_vec1 = np.array( [ df_couple['pos2X'] - df_couple['pos1X'] , \
								   df_couple['pos2Y'] - df_couple['pos1Y'] ] ).flatten()

			dir_vec2 = np.array( [ df_couple['pos1X'] - df_couple['pos2X'] , \
								   df_couple['pos1Y'] - df_couple['pos2Y'] ] ).flatten()

			angle1 = np.arctan2(dir_vec1[1], dir_vec1[0])
			angle2 = np.arctan2(dir_vec2[1], dir_vec2[0])

			x1_force = np.cos(angle1)*df_couple['force'].values[0]
			y1_force = np.sin(angle1)*df_couple['force'].values[0]

			x2_force = np.cos(angle2)*df_couple['force'].values[0]
			y2_force = np.sin(angle2)*df_couple['force'].values[0]

			cluster_id = df_couple['cluster'].values[0]

			if self.args.largest:
				if cluster_id == self.largest_cluster_id:
					(x1_force_sum, y1_force_sum, x2_force_sum, y2_force_sum ) \
							  = self.write_to_dataframe(couple_id, cluster_id, \
												   x1_force, y1_force, \
												   x2_force, y2_force, \
												   x1_force_sum, y1_force_sum, \
												   x2_force_sum, y2_force_sum)
			else:
				(x1_force_sum, y1_force_sum, x2_force_sum, y2_force_sum ) \
						  = self.write_to_dataframe(couple_id, cluster_id, \
											   x1_force, y1_force, \
											   x2_force, y2_force, \
											   x1_force_sum, y1_force_sum, \
											   x2_force_sum, y2_force_sum)

		sum_output = {"fx1_sum": x1_force_sum,\
					  "fy1_sum": y1_force_sum,\
					  "fx2_sum": x2_force_sum,\
					  "fy2_sum": y2_force_sum}

		self.sum_output_df = pd.DataFrame([sum_output])


	def analyze_forces(self):
		self.calc_force_vec()
		self.write_output_file()

	def get_file_paths(self):
		super().get_file_paths()

		sum_output_file_path = self.file_dict["input"]["path"].with_suffix(".sum.dat")
		sum_output_file_name = sum_output_file_path.name

		sum_dict = {"name": sum_output_file_name, "path": sum_output_file_path}

		self.file_dict["sum"] = sum_dict

	def write_output_file(self):
		super().write_output_file()

		self.sum_output_df.to_csv(self.file_dict["sum"]["path"], float_format='%.5f', header=True, index=None, sep="\t")


column_list = [ 'identity', 'cluster', 'force', 'cos_angle', 'pos1X', 'pos1Y', 'pos2X', 'pos2Y' ]
myCoupleForces = CoupleForces(column_list)
myCoupleForces.analyze_forces()
del myCoupleForces
