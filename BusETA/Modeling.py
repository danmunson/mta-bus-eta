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
from sklearn.externals import joblib
from collections import Counter
import random
from BusETA import DataCollection as Dc



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
            
            csv_files = []
            for fl in files:
                ext = os.path.splitext(fl)[1]
                if ext == '.csv':
                    csv_files.append(fl)
            
            file1 = csv_files.pop(0)
            file1path = os.path.join(root, file1)
            start_df = pd.read_csv(file1path, header = 0)
            full = start_df
            
            for fl in csv_files:
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

    @classmethod  #standard linear model transform
    def std_lm_transform(cls, df, poly, drop_one):
        new_df = cls.continuousToD_dummyDoW(df, drop_one)
        new_df = cls.poly_ToD(new_df, poly)
        new_df = cls.dummify_postat(new_df, drop_one)
        return new_df

    @classmethod
    def apply_SLT(cls, dfs, poly = 1, drop_one=True):
        new_df_dict = {}
        for name, df in dfs.iteritems():
            new_df = cls.std_lm_transform(df, poly, drop_one)
            new_df_dict[name] = new_df
            print 'transformed ' + name
        return new_df_dict

    @classmethod  #standard decision tree transform
    def std_dt_transform(cls, df):
        new_df = cls.separate_ToD_DoW(df)
        return new_df

    @classmethod
    def apply_SDT(cls, dfs):
        new_df_dict = {}
        for name, df in dfs.iteritems():
            new_df = cls.std_dt_transform(df)
            new_df_dict[name] = new_df
            print 'transformed ' + name
        return new_df_dict

    @classmethod
    def separate_ToD_DoW(cls, df):
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
        return newdf

    @classmethod
    def dummify_postat(cls, df, drop_one):
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
        frame = pd.get_dummies(dummdf.ix[:,'Postat'], drop_first=drop_one)
        dummdf = pd.concat([dummdf, frame], axis=1)
        del dummdf['Postat']
        return dummdf

    @classmethod
    def continuousToD_dummyDoW(cls, df, drop_one):
        newdf = cls.separate_ToD_DoW(df)
        frame = pd.get_dummies(newdf.ix[:,'DayOfWeek'], drop_first=drop_one)
        cols = []
        for day in list(frame.columns):
            cols.append('day:'+str(day))
        frame.columns = cols
        newdf = pd.concat([newdf, frame], axis=1)
        del newdf['DayOfWeek']
        return newdf

    @classmethod    #converts time_of_day variable into a polynomial set of variables
    def poly_ToD(cls, df, order): 
        time_of_day = pd.DataFrame(df['TimeOfDay'])
        poly_ftrs = prep.PolynomialFeatures(degree=order)
        poly_tod = pd.DataFrame(poly_ftrs.fit_transform(time_of_day))
        new_df = df
        del new_df['TimeOfDay']
        cols = []
        for i in range(order+1):
            cols.append('t^'+str(i))
        poly_tod.columns = cols
        new_df = pd.concat([new_df,poly_tod], axis=1)
        return new_df
        
class Eval:

    @classmethod    #returns a df that shows the mean & std of the cross-validated eval_metric for each stop and each model
    def cv_matrix(cls, dfs, models, cv_folds = 5, eval_metric='neg_mean_absolute_error'):
        stop_scores = []
        iterations = len(dfs)*len(models)
        count = 1
        for stop_name, dfi in dfs.iteritems():
            df = dfi.copy()
            response = np.ravel(pd.DataFrame(df.pop('TimeDelta')))
            predictors = df
            scores = {}
            scores['stop'] = stop_name
            for name, model in models.iteritems():
                mod_inst = model
                cv_accuracy = mods.cross_val_score(mod_inst, predictors, response, cv=cv_folds, scoring=eval_metric)
                print 'finished '+ str(count)+ '/'+ str(iterations)
                avg = cv_accuracy.mean()
                st_d = cv_accuracy.std()
                scores[name+':avg'] = avg
                scores[name+':std'] = st_d
                count += 1
            stop_scores.append(scores)
        
        return pd.DataFrame(stop_scores)


class Persistence:

    @classmethod
    def train_and_save(cls, dfi, model, stop_path):
        df = dfi.copy()
        response = pd.DataFrame(df.pop('TimeDelta'))
        predictors = df
        model_inst = model
        model_inst.fit(predictors, response)

        model_filename = os.path.join(stop_path, 'active_model.pkl')
        meta_filename = os.path.join(stop_path, 'model_columns.txt')

        if os.path.isfile(model_filename):
            os.remove(model_filename)
            joblib.dump(model_inst, model_filename)
        else:
            joblib.dump(model_inst, model_filename)
        
        meta = io.open(meta_filename, 'w')
        for col in list(predictors.columns):
            meta.write(unicode(col+'\n'))
        meta.close()

        return

    @classmethod
    def train_save_route(cls, dfs, model):
        for stop_name, dfi in dfs.iteritems():
            cls.train_and_save(dfi, model, stop_name)
        return

    @classmethod
    def get_stop_model(cls, dirpath):
        path = os.path.join(dirpath,'active_model.pkl')
        return joblib.load(path)

    @classmethod
    def get_lm_prediction_input(cls, predictors, metafile): ## metafile is needed because # of columns can differ
        predictor_vec = {}
        column = metafile.readline().strip()
        while column != '':
            if column[0:4] == 'day:':   #must represent day of week
                day = column.split(':')[1]
                if day == str(predictors['day']):
                    predictor_vec[column] = [1]
                else:
                    predictor_vec[column] = [0]
            elif column[0:2] == 't^':   #must represent hours
                order = float(column.split('^')[1])
                poly_hr = predictors['hour'] ** order
                predictor_vec[column] = [poly_hr]
            else:   #must represent a postat
                if column == predictors['postat']:
                    predictor_vec[column] = [1]
                else:
                    predictor_vec[column] = [0]
            column = metafile.readline().strip()
        
        pred_vec = pd.DataFrame(predictor_vec)
        positives = {}
        for k, el in predictor_vec.iteritems():
            if el[0] != 0:
                positives[k] = el[0]

        return pred_vec, positives

    @classmethod
    def get_dt_prediction_input(cls, predictors): ## no metafile needed because columns are pre-determined
        predictor_vec = {}
        predictor_vec['DayOfWeek'] = predictors['day']
        predictor_vec['TimeOfDay'] = predictors['hour']

        split_postat = predictors['postat'].split(':')
        predictor_vec['Position'] = split_postat[0]
        status = split_postat[1]
        if status[-10:] == 'miles away':
            predictor_vec['Status'] = status[1:]
        else:
            predictor_vec['Status'] = status

        pred_vec = pd.DataFrame(predictor_vec)
        return pred_vec, predictor_vec
