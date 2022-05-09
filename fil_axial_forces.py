from data_class import Data
import numpy as np
import pandas as pd

class FilAxialForces(Data):
	def __init__(self, column_list):
		super(). __init__(column_list=column_list)

		self.fil_force_df = pd.DataFrame(columns=[ 'fil_id', 'fx', 'fy' ])
		self.sum_output_df = pd.DataFrame()

	def calc_force_vec_proj(self, fil_vec, force_vec):

		return fil_vec * np.dot(fil_vec, force_vec) / np.dot(fil_vec, fil_vec)

	def calc_fil_forces(self):

		for couple_id, df_couple in self.temp_dataframe.groupby('identity'):
			cpl_dir1 = np.array( [ df_couple['pos2X'] - df_couple['pos1X'] , \
							  df_couple['pos2Y'] - df_couple['pos1Y'] ] ).flatten()

			cpl_dir2 = np.array( [ df_couple['pos1X'] - df_couple['pos2X'] , \
							  df_couple['pos1Y'] - df_couple['pos2Y'] ] ).flatten()

			fil_dir1 = np.array( [ df_couple['dirFiber1X'], df_couple['dirFiber1Y'] ] ).flatten()
			fil_dir2 = np.array( [ df_couple['dirFiber2X'], df_couple['dirFiber2Y'] ] ).flatten()

			force_mag = df_couple['force'].values[0]

			cluster_id = df_couple['cluster'].values[0]
			fil_id1 = df_couple['fiber1'].values[0]
			fil_id2 = df_couple['fiber2'].values[0]

			if self.args.largest:
				if cluster_id == self.largest_cluster_id:
					f_vec1 = force_mag * self.calc_force_vec_proj(fil_dir1, cpl_dir1)
					f_vec2 = force_mag * self.calc_force_vec_proj(fil_dir2, cpl_dir2)

					new_df1 = pd.DataFrame( [[ fil_id1, f_vec1[0], f_vec1[1] ]],\
											columns = [ "fil_id", "fx", "fy" ])


					new_df2 = pd.DataFrame( [[ fil_id2, f_vec2[0], f_vec2[1] ]],\
											columns = [ "fil_id", "fx", "fy" ])
			else:
				f_vec1 = force_mag * self.calc_force_vec_proj(fil_dir1, cpl_dir1)
				f_vec2 = force_mag * self.calc_force_vec_proj(fil_dir2, cpl_dir2)

				new_df1 = pd.DataFrame( [[ fil_id1, f_vec1[0], f_vec1[1] ]],\
										columns = [ "fil_id", "fx", "fy" ])


				new_df2 = pd.DataFrame( [[ fil_id2, f_vec2[0], f_vec2[1] ]],\
										columns = [ "fil_id", "fx", "fy" ])




			self.fil_force_df = pd.concat([self.fil_force_df, new_df1], ignore_index=True)
			self.fil_force_df = pd.concat([self.fil_force_df, new_df2], ignore_index=True)

		for fil_id, fil_df in self.fil_force_df.groupby("fil_id"):
			fx_sum = fil_df['fx'].sum()
			fy_sum = fil_df['fy'].sum()

			new_df = pd.DataFrame( [[ fil_id, fx_sum, fy_sum ]], columns=[ "fil_id", "fx_sum", "fy_sum" ])

			self.output_df = pd.concat([self.output_df, new_df], ignore_index=True)

		fx_sum = self.output_df["fx_sum"].sum()
		fy_sum = self.output_df["fy_sum"].sum()

		self.sum_output_df = pd.DataFrame( [[ fx_sum, fy_sum ]], columns=["fx_sum", "fy_sum"])

	def analyze_forces(self):
		self.calc_fil_forces()
		self.write_output_file()

	def get_file_paths(self):
		super().get_file_paths()

		sum_output_file_path = self.file_dict["input"]["path"].with_suffix(".sum.dat")
		sum_output_file_name = sum_output_file_path.name

		sum_dict = {"name": sum_output_file_name, "path": sum_output_file_path}

		self.file_dict["sum"] = sum_dict

		fil_output_file_path = self.file_dict["input"]["path"].with_suffix(".fil.dat")
		fil_output_file_name = fil_output_file_path.name

		fil_dict = {"name": fil_output_file_name, "path": fil_output_file_path}

		self.file_dict["fil"] = fil_dict

	def write_output_file(self):
		super().write_output_file()

		self.sum_output_df.to_csv(self.file_dict["sum"]["path"], float_format='%.5f', header=True, index=None, sep="\t")

		self.fil_force_df.to_csv(self.file_dict["fil"]["path"], float_format='%.5f', header=False, index=None, sep="\t")
#
column_list = [ 'identity', 'cluster', 'force', \
				'pos1X', 'pos1Y', 'fiber1', 'dirFiber1X', 'dirFiber1Y', \
				'pos2X', 'pos2Y', 'fiber2', 'dirFiber2X', 'dirFiber2Y' ]
myFilAxialForces = FilAxialForces(column_list)
myFilAxialForces.analyze_forces()
del myFilAxialForces
