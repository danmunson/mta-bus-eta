from BusETA import Modeling as md
import os
import sys
from sklearn import linear_model, tree, ensemble, svm

read_stops = md.Read.read_all_stops
featurize = md.FeatureEng.apply_st
save = md.Persistence.train_save_route

route = sys.argsv[1]
a = sys.argsv[2]
