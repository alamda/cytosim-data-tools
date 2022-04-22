from data_class import Data
import pandas as pd

class Cluster(Data):
	def __init__(self, column_list=['class','identity']):
		super().__init__()

		self.get_relevant_columns(column_list)

		if (self.args.largest == True) and ('cluster' in self.temp_dataframe.columns) :
			self.largest_cluster_id = self.get_largest_cluster_id() ;
			self.get_largest_cluster_data()

		self.total_num_fils = self.get_num_fils()
		self.total_num_couples = self.get_num_couples()
		self.ratio_couples_to_fils = self.total_num_couples / self.total_num_fils

		(self.num_parallel_fil_pairs, self.num_antiparallel_fil_pairs) = self.get_num_parallel_fil_pairs()
		self.ratio_parallel_fil_pairs = self.num_parallel_fil_pairs / self.total_num_couples
		self.ratio_antiparallel_fil_pairs = self.num_antiparallel_fil_pairs / self.total_num_couples

		(self.num_parallel_fils, self.num_antiparallel_fils, self.num_unique_fil_pairs) = self.count_parallel_fils()
		self.ratio_parallel_fils = self.num_parallel_fils / self.num_unique_fil_pairs
		self.ratio_antiparallel_fils = self.num_antiparallel_fils / self.num_unique_fil_pairs

		output = {'Nf':		self.total_num_fils, \
				  'Nc':		self.total_num_couples, \
				  'Rcf':	self.ratio_couples_to_fils, \
				  'Npc':		self.num_parallel_fil_pairs, \
				  'Rpc':	self.ratio_parallel_fil_pairs, \
				  'Nac':		self.num_antiparallel_fil_pairs, \
				  'Rac':	self.ratio_antiparallel_fil_pairs,\
				  'Nufp':		self.num_unique_fil_pairs,\
				  'Npf':		self.num_parallel_fils,\
				  'Rpf':	self.ratio_parallel_fils,\
				  'Naf':		self.num_antiparallel_fils,\
				  'Raf':	self.ratio_antiparallel_fils}

		self.output_df = pd.DataFrame([output])

		self.write_output_file()

		self.delete_temp_file()


	def get_largest_cluster_id(self):
		return self.temp_dataframe['cluster'].mode().values[0]

	def get_largest_cluster_data(self):
		for cluster_id, df_cluster in self.temp_dataframe.groupby('cluster'):
			if cluster_id == self.largest_cluster_id:
				self.temp_dataframe = df_cluster
				self.write_temp_dataframe()

	def get_num_fils(self):
		fiber_ids_df = pd.concat([self.temp_dataframe['fiber1'], self.temp_dataframe['fiber2']], ignore_index=True)

		return len(fiber_ids_df.drop_duplicates())

	def get_num_couples(self):
		couple_ids_df = self.temp_dataframe['identity']

		return len(couple_ids_df.drop_duplicates())

	def get_num_parallel_fil_pairs(self):
		num_parallel_fil_pairs = 0
		num_antiparallel_fil_pairs = 0

		for couple_id, df_couple in self.temp_dataframe.groupby('identity'):
			if df_couple['cos_angle'].values[0] > 0:
				num_parallel_fil_pairs += 1
			else:
				num_antiparallel_fil_pairs += 1

		return (num_parallel_fil_pairs, num_antiparallel_fil_pairs)

	def count_parallel_fils(self):
		num_parallel_fils = 0
		num_antiparallel_fils = 0
		num_unique_fil_pairs = 0

		for fil1_id, df_fil1 in self.temp_dataframe.groupby('fiber1'):
			num_parallel_fils += len(df_fil1['fiber2'][df_fil1['cos_angle']>0].drop_duplicates())
			num_antiparallel_fils += len(df_fil1['fiber2'][df_fil1['cos_angle']<= 0].drop_duplicates())

			num_unique_fil_pairs += len(df_fil1['fiber2'].drop_duplicates())

		return (num_parallel_fils, num_antiparallel_fils, num_unique_fil_pairs)


column_list = ['identity', 'fiber1', 'fiber2', 'cos_angle', 'cluster']
myCluster = Cluster(column_list)
