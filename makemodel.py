#make a model
import sys
sys.path.insert(0,'/usr/local/lib/python2.7/site-packages')
from BusETA import Modeling
from sklearn import metrics, linear_model
from sklearn import model_selection as mods


get_stop_paths = Modeling.Read.get_stop_paths
get_stop_data = Modeling.Read.read_stop_data
stratify = Modeling.Tools.stratify_by_hour
dummify = Modeling.FeatureEng.dummify_pos_stat_time
dummy_lm = Modeling.LinearModels.ols_dummies_crossval

name = raw_input('Route name: ')

paths = get_stop_paths('Routes/'+name)

dfs = {}
for path in paths:
    try:
        df = get_stop_data(path)
        dfs[path] = df
    except Exception as e:
        print(e)

#for each stopdf: stratify data by the hour, convert to dummy vals, fit model
for k, df in dfs.iteritems():
    print k + ':'
    strat_df = stratify(df, 'Timestamp')
    print strat_df.shape
    print strat_df.head()
    try:
        dum_df = dummify(strat_df)
        cv_eval = dummy_lm(dum_df, linear_model.LinearRegression(), 'neg_mean_absolute_error')
        print 'MADs:  ' + str(cv_eval) 
    except Exception as e:
        print e
    print '--------------'