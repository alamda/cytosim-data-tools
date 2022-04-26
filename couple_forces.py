from cluster_analysis import Cluster

class CoupleForces(Cluster):
    def __init__(self):
        super().__init__()

    def write_to_dataframe(self, couple_id, cluster_id, \
    					   x1_force, y1_force, x2_force, y2_force, \
    					   x1_force_sum, y1_force_sum, x2_force_sum, y2_force_sum):

    	new_df1 = pd.DataFrame([[ couple_id, cluster_id, \
    							  x1_force, y1_force ]],\
    						      columns=[ 'identity', 'cluster',\
    							   			'x1_force', 'y1_force' ])

    	new_df2 = pd.DataFrame([[ couple_id, cluster_id, \
    							  x2_force, y2_force ]],\
    						  	  columns=[ 'identity', 'cluster', \
    							  			'x2_force', 'y2_force' ])

    	new_df_both = new_df1.merge(new_df2, on=["identity","cluster"])

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
    						  = write_to_dataframe(couple_id, cluster_id, \
    											   x1_force, y1_force, \
    											   x2_force, y2_force, \
    											   x1_force_sum, y1_force_sum, \
    											   x2_force_sum, y2_force_sum)
    		else:
    			(x1_force_sum, y1_force_sum, x2_force_sum, y2_force_sum ) \
    					  = write_to_dataframe(couple_id, cluster_id, \
    										   x1_force, y1_force, \
    										   x2_force, y2_force, \
    										   x1_force_sum, y1_force_sum, \
    										   x2_force_sum, y2_force_sum)
    def analyze_forces(self):
        self.calc_force_vec()
        self.write_output_file()

column_list = [ 'identity', 'cluster', 'force', 'cos_angle', 'pos1X', 'pos1Y', 'pos2X', 'pos2Y' ]
myCoupleForces = CoupleForces()
myCoupleForces.analyze_forces()
del myCoupleForces
