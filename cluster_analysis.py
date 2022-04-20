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

        output = {'N_fil':                self.total_num_fils, \
                  'N_cpl':             self.total_num_couples, \
                  'N_cpl:N_fil':         self.ratio_couples_to_fils, \
                  'N_para':        self.num_parallel_fil_pairs, \
                  'N_para:N_cpl':       self.ratio_parallel_fil_pairs, \
                  'N_antipara':    self.num_antiparallel_fil_pairs, \
                  'N_antipara:N_cpl':   self.ratio_antiparallel_fil_pairs}

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



column_list = ['identity', 'fiber1', 'fiber2', 'cos_angle', 'cluster']
myCluster = Cluster(column_list)
