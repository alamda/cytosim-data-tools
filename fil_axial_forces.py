from data_class import Data
import numpy as np
import pandas as pd

class FilAxialForces(Data):
	def __init__(self, column_list):
		super(). __init__(column_list=column_list)

		self.fil_force_df = pd.DataFrame(columns=[ 'fil_id', 'f' ])
		self.sum_output_df = pd.DataFrame()

	def normalize(self, vec):
		norm = np.linalg.norm(vec)
		if norm == 0:
			return vec
		return vec / norm

	def calc_dot_prod(self, fil_vec, force_vec):

		# Normalize the vectors
		fil_vec = self.normalize(fil_vec)
		force_vec = self.normalize(force_vec)
		return np.dot(fil_vec, force_vec)

	def calc_fil_forces(self):

		for couple_id, df_couple in self.temp_dataframe.groupby('identity'):
			# Get direction vectors of of forces exerted by motor hands
			cpl_dir1 = np.array( [ df_couple['pos2X'] - df_couple['pos1X'] , \
							  df_couple['pos2Y'] - df_couple['pos1Y'] ] ).flatten()

			cpl_dir2 = np.array( [ df_couple['pos1X'] - df_couple['pos2X'] , \
							  df_couple['pos1Y'] - df_couple['pos2Y'] ] ).flatten()

			# Get direction vector of filaments
			fil_dir1 = np.array( [ df_couple['dirFiber1X'], df_couple['dirFiber1Y'] ] ).flatten()
			fil_dir2 = np.array( [ df_couple['dirFiber2X'], df_couple['dirFiber2Y'] ] ).flatten()

			# Get the magnitude of the force
			force_mag = df_couple['force'].values[0]

			# Get indexes of motor and filaments
			cluster_id = df_couple['cluster'].values[0]
			fil_id1 = df_couple['fiber1'].values[0]
			fil_id2 = df_couple['fiber2'].values[0]

			if self.args.largest:
				if cluster_id == self.largest_cluster_id:
					# Need to multiply force magnitude bc direction vectors should be (?) unit vectors
					f1 = force_mag * self.calc_dot_prod(fil_dir1, cpl_dir1)
					f2 = force_mag * self.calc_dot_prod(fil_dir2, cpl_dir2)

					new_df1 = pd.DataFrame( [[ fil_id1, f1 ]],\
											columns = [ "fil_id", "f" ])


					new_df2 = pd.DataFrame( [[ fil_id2, f2 ]],\
											columns = [ "fil_id", "f" ])
			else:
				f1 = force_mag * self.calc_dot_prod(fil_dir1, cpl_dir1)
				f2 = force_mag * self.calc_dot_prod(fil_dir2, cpl_dir2)

				new_df1 = pd.DataFrame( [[ fil_id1, f1 ]],\
										columns = [ "fil_id", "f" ])


				new_df2 = pd.DataFrame( [[ fil_id2, f2 ]],\
										columns = [ "fil_id", "f" ])

			self.fil_force_df = pd.concat([self.fil_force_df, new_df1], ignore_index=True)
			self.fil_force_df = pd.concat([self.fil_force_df, new_df2], ignore_index=True)

		# find the total force along each filament
		for fil_id, fil_df in self.fil_force_df.groupby("fil_id"):
			f_sum = fil_df['f'].sum()

			new_df = pd.DataFrame( [[ fil_id, f_sum ]], columns=[ "fil_id", "f_sum" ])

			self.output_df = pd.concat([self.output_df, new_df], ignore_index=True)

		f_sum = self.output_df["f_sum"].sum()

		self.sum_output_df = pd.DataFrame( [[ f_sum ]], columns=["f_sum"])

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
