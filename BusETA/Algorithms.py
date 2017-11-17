# learning algorithm implementations
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


class MedianLookup():

    predictions = {}    # {value}
    time_blocks = None

    def fit(self, predictors, response):
        self.time_blocks = predictors['TimeOfDay'].max() + 1
        df = pd.concat([predictors.copy(), response.copy()], axis=1)
        groups = df.groupby(['Position','Status','DayOfWeek','TimeOfDay'])
        self.predictions = dict(groups.TimeDelta.median())
        return

    def predict(self, pv):
        hour = int(pv['TimeOfDay'])
        divisor = int(24/self.time_blocks)
        block = int(hour/divisor)
        key = (float(pv['Position']), pv['Status'], pv['DayOfWeek'], block)
        median = self.predictions[key]
        return median