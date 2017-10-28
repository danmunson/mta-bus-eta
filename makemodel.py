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


paths = get_stop_paths('Routes/M60')

dfs = {}
for path in paths:
    try:
        df = get_stop_data(path)
        dfs[path] = df
    except Exception as e:
        print(e)


for k, df in dfs.iteritems():
    #stratify data by the hour, convert to dummy vals, fit model
    strat_df = stratify(df, 'Timestamp')
    dum_df = dummify(strat_df)
    cv_eval = dummy_lm(dum_df, linear_model.LinearRegression(), ['neg_mean_absolute_error', 'neg_median_absolute_error', 'r2'])
    for score, val in cv_eval.iteritems():
        print score + ':  ' + str(val) 

    print '--------------'