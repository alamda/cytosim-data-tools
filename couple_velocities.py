from data_class import Data
from fil_axial_forces import FilAxialForces

import sys
from pathlib import Path
import pandas as pd

class CoupleVelocities(FilAxialForces):
	def __init__(self, column_list, argv=sys.argv[1:]):
		super().__init__(column_list=column_list)

		self.get_args(argv)
		self.get_file_paths()
		self.get_motor_params()

		self.calc_fil_forces()
		self.fil_force_df = self.output_df
		self.output_df = pd.DataFrame()

	def get_args(self, argv):
		Data.get_args(self, argv)

		# TODO: does not work correctly when -c flag is passed with file name
		# Works with the default value
		# Need to fix

		self.parser.add_argument('--cfile', '-c', type=str, help='', default="config.cym")

		self.args = self.parser.parse_args(argv)

	def get_file_paths(self):
		Data.get_file_paths(self)

		config_file_name = self.args.cfile
		config_file_path = Path(config_file_name)

		config_dict = {"name": config_file_name, "path": config_file_path}

		self.file_dict["config"] = config_dict

	def get_motor_params(self):
		with open(self.file_dict["config"]["path"]) as file:
			for line in file.readlines():
				if "unloaded_speed" in line.strip():
					self.unloaded_speed = float(line.strip().split('=')[-1])
				elif "stall_force" in line.strip():
					self.stall_force = float(line.strip().split('=')[-1])

	def calc_motor_vel(self):
		for couple_id, df_couple in self.temp_dataframe.groupby('identity'):
			fil1_id = df_couple['fiber1'].values[0]
			fil1_force = self.fil_force_df[self.fil_force_df['fil_id']==fil1_id]['f_sum'].values[0]

			fil2_id = df_couple['fiber2'].values[0]
			fil2_force = self.fil_force_df[self.fil_force_df['fil_id']==fil2_id]['f_sum'].values[0]

			v1 = self.unloaded_speed * (1 + fil1_force /self.stall_force)

			v2 = self.unloaded_speed * (1 + fil2_force / self.stall_force)

			new_df1 = pd.DataFrame( [[ couple_id, fil1_id, v1 ]], columns = ["cpl_id", "fil_id", "v"])

			new_df2 = pd.DataFrame( [[ couple_id, fil2_id, v2 ]], columns = ["cpl_id", "fil_id", "v"])

			self.output_df = pd.concat([self.output_df, new_df1], ignore_index=True)
			self.output_df = pd.concat([self.output_df, new_df2], ignore_index=True)

	def write_output_file(self):
		Data.write_output_file(self)

	def analyze_vel(self):
		self.calc_motor_vel()
		self.write_output_file()

if __name__=="__main__":

	column_list = [ 'identity', 'cluster', 'force', \
					'pos1X', 'pos1Y', 'fiber1', 'dirFiber1X', 'dirFiber1Y', \
					'pos2X', 'pos2Y', 'fiber2', 'dirFiber2X', 'dirFiber2Y' ]

	myCoupleVelocities = CoupleVelocities(column_list)
	myCoupleVelocities.analyze_vel()
	del myCoupleVelocities
