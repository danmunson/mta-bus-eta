#make a model

from BusETA import Modeling
from sklearn import metrics, linear_model
from sklearn import model_selection as mods


get_stop_paths = Modeling.Read.get_stop_paths
get_stop_data = Modeling.Read.read_stop_data
dum_pst = Modeling.FeatureEng.dummify_pos_stat_time

name = raw_input('Route name: ')
paths = get_stop_paths('Routes/'+name)
stop_dfs = {}
for path in paths:
    stop_dfs[path] = get_stop_data(path)


