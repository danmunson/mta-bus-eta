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
from sklearn import preprocessing as prep
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
                
                full = pd.concat([full, df], axis = 'index', ignore_index=True)
        return full

    @classmethod
    def read_all_stops(cls, route_name):
        paths = cls.get_stop_paths('Routes/'+route_name)
        stop_dfs = {}
        for path in paths:
            try:
                stop_dfs[path] = cls.read_stop_data(path)
                print 'loaded ' + path
            except Exception as e:
                print e
        return stop_dfs

class FeatureEng:

    @classmethod
    def std_transform(cls, df, poly, pos_only):
        new_df = cls.continuousToD_dummyDoW(df)
        new_df = cls.poly_ToD(new_df, poly)
        if pos_only:
            new_df = cls.dummify_pos_only(new_df)
        else:
            new_df = cls.dummify_postat(new_df)
        return new_df

    @classmethod
    def lapply_st(cls, dfs, poly = 1, pos_only = False):
        new_df_dict = {}
        for name, df in dfs.iteritems():
            new_df = cls.std_transform(df, poly, pos_only)
            new_df_dict[name] = new_df
            print 'transformed ' + name
        return new_df_dict

    @classmethod
    def dummify_postat(cls, df):
        dummdf = df.copy()
        for i in range(dummdf.shape[0]):
            status = dummdf.ix[i,'Status']
            if status[-10:] == 'miles away':
                dummdf.ix[i,'Status'] = status[1:]
        postats = []
        for i in range(dummdf.shape[0]):
            position = dummdf.ix[i,'Position']
            status = dummdf.ix[i,'Status']
            postat = str(position)+':'+status
            postats.append(postat)
        dummdf['Postat'] = pd.Series(postats)
        del dummdf['Position']
        del dummdf['Status']
        frame = pd.get_dummies(dummdf.ix[:,'Postat'])
        dummdf = pd.concat([dummdf, frame], axis=1)
        del dummdf['Postat']
        return dummdf

    @classmethod
    def dummify_pos_only(cls,df):
        dummdf = df.copy()     
        poss = []
        for i in range(dummdf.shape[0]):
            position = dummdf.ix[i,'Position']
            poss.append(position)
        dummdf['Pos'] = pd.Series(poss)
        del dummdf['Position']
        del dummdf['Status']
        frame = pd.get_dummies(dummdf.ix[:,'Pos'])
        dummdf = pd.concat([dummdf, frame], axis=1)
        del dummdf['Pos']
        return dummdf

    @classmethod
    def continuousToD_dummyDoW(cls, df):
        newdf = df.copy()
        times = pd.to_datetime(newdf.ix[:,'Timestamp'], format='%Y-%m-%d %H:%M:%S.%f')
        days = []
        hours = []
        for time in list(times):
            hours.append(time.hour + (time.minute/60.0))
            days.append(time.weekday())
        newdf['TimeOfDay'] = pd.Series(hours)
        newdf['DayOfWeek'] = pd.Series(days)
        del newdf['Timestamp']
        frame = pd.get_dummies(newdf.ix[:,'DayOfWeek'])
        newdf = pd.concat([newdf, frame], axis=1)
        del newdf['DayOfWeek']
        return newdf

    @classmethod
    def poly_ToD(cls, df, order):
        time_of_day = pd.DataFrame(df['TimeOfDay'])
        poly_ftrs = prep.PolynomialFeatures(degree=order)
        poly_tod = pd.DataFrame(poly_ftrs.fit_transform(time_of_day))
        new_df = df
        del new_df['TimeOfDay']
        new_df = pd.concat([new_df,poly_tod], axis=1)
        return new_df
        
class Eval:

    @classmethod
    def compare_cv_scores(cls, dfs, models, cv_folds = 10):
        stop_scores = []
        for stop_name, df in dfs.iteritems():
            response = pd.DataFrame(df.pop('TimeDelta'))
            predictors = df
            scores = {}
            scores['stop'] = stop_name
            for name, model in models.iteritems():
                mod_inst = model
                cv_accuracy = list(mods.cross_val_score(mod_inst, predictors, response, cv=cv_folds))
                total = 0
                for acc in cv_accuracy:
                    total += acc
                scores[name] = total/float(cv_folds)
            stop_scores.append(scores)
        
        return pd.DataFrame(stop_scores)