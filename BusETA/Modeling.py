#model building
import sys
import requests as req
import numpy as np
import io
import pandas as pd
from bs4 import BeautifulSoup as BS
import datetime
import unicodedata
import os, shutil
import sys
from sklearn import linear_model, metrics
from sklearn import model_selection as mods
from collections import Counter
import random


class Read:
    
    @classmethod
    def get_stop_paths(cls, route_path):
        stop_paths = []
        #get direction paths
        direction_paths = []
        for root, dirs, files in os.walk(route_path):
            for dirc in dirs:
                direction_paths.append(os.path.join(route_path, dirc))
            break
        #get stop paths
        for path in direction_paths:
            for root, dirs, files in os.walk(path):
                for dirc in dirs:
                    stop_paths.append(os.path.join(path, dirc))
                break
        return stop_paths

    @classmethod
    def read_stop_data(cls, stop_path):
        full = None
        for root, dirs, files in os.walk(stop_path):
            file1 = files.pop(0)
            file1path = os.path.join(root, file1)
            start_df = pd.read_csv(file1path, header = 0)
            full = start_df
            
            for fl in files:
                path = os.path.join(root, fl)
                df = pd.read_csv(path, header = 0)
                
                full = pd.concat([full, df], axis = 1)
        return full


class FeatureEng:

    @classmethod
    def dummify_pos_stat_time(cls, df):
        dummdf = df.copy()
        times = pd.to_datetime(dummdf.ix[:,'Timestamp'], format='%Y-%m-%d %H:%M:%S.%f')
        
        days = []
        hours = []
        for time in list(times):
            hours.append(time.hour)
            days.append(time.weekday())
        dummdf['Hours'] = pd.Series(hours)
        dummdf['Days'] = pd.Series(days)
        del dummdf['Timestamp']

        for i in range(dummdf.shape[0]):
            status = dummdf.ix[i,'Status']
            if status[-10:] == 'miles away':
                dummdf.ix[i,'Status'] = status[1:]        

        count = 0
        postats = []
        for i in range(dummdf.shape[0]):
            position = dummdf.ix[i,'Position']
            status = dummdf.ix[i,'Status']
            postat = str(position)+':'+status
            postats.append(postat)
        dummdf['Postat'] = pd.Series(postats)
        del dummdf['Position']
        del dummdf['Status']

        for col in ['Hours', 'Days', 'Postat']:
            frame = pd.get_dummies(dummdf.ix[:,col])
            dummdf = pd.concat([dummdf, frame], axis=1)
            del dummdf[col]

        return dummdf

class LinearModels:

    @classmethod
    def ols_dummies_crossval(cls, df, estim, scores):
        response = df.pop('TimeDelta')
        predictors = df
        cvscores = mods.cross_val_score(estim, predictors, response, scoring=scores)
        return cvscores


class Tools:

    @classmethod
    def crossvalidate(cls, folds):
        
        pass


    ## should be used before converting variables to dummies
    ## this process aims to maximize obs-ct while maintaining equal representation among all values of the given column
    @classmethod
    def stratify_by_hour(cls, df, colname):
        hours = []
        timeser = pd.to_datetime(df.ix[:,colname], format='%Y-%m-%d %H:%M:%S.%f')
        for i in range(len(timeser)):
            hour = timeser[i].hour
            hours.append(str(hour))
        hour_ct = Counter(hours)
        minV = None
        assign = True
        for k, v in hour_ct.iteritems():
            if assign:
                assign = False
                minV = v
                continue
            if v < minV:
                minV = v
        selection_prob = {}
        
        for k, v in hour_ct.iteritems():
            p = float(minV/v)
            selection_prob[k] = p
        
        added = []
        for i in range(df.shape[0]):
            p = selection_prob[hours[i]]
            threshold = random.uniform(0,1)
            if p >= threshold:
                obs = df.ix[i,:]
                added.append(obs)
        
        strat_df = pd.DataFrame(added)        

        return strat_df

                



