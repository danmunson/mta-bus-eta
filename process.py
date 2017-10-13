import requests as req
import io
import pandas as pd
from bs4 import BeautifulSoup as BS
import datetime
import unicodedata
import os, shutil
from BusETA import DataTransforms
from BusETA import DataCollection
import sys

#fixes an encoding problem
reload(sys)  
sys.setdefaultencoding('utf8')

cursor = DataTransforms.Transforms.cursor
prepper = DataTransforms.Transforms.prepare_dataframe
dirsplitter = DataTransforms.Transforms.split_directions
normalize = DataCollection.GetBusData.normalize

#get route dict and list of all routes
route_df = pd.read_csv('./route_dict.csv', header=None)
routes = list(route_df.ix[:,0])

print '** Commence processing **'

for route in routes:

    raw_data_path = 'Routes/'+route+'/stopdata.csv'

    posdf = pd.read_csv('Routes/'+route+'/positioning.csv', header=None)
    rawdf = prepper(raw_data_path, posdf)
    dir_wise, stop_names = dirsplitter(rawdf, 'approaching')

    for i in range(len(dir_wise)):
        dir_df = dir_wise[i]
        dir = dir_df.ix[0,'Direction']

        stop_names = list(set(list(dir_df.ix[:,'Stop'])))
        for stop in stop_names:
            stopnm = stop
            accum = [] #columns=['Position', 'Status', 'Timestamp', 'TimeDelta'])

            #process data for a given stop
            cursor(dir_df, accum, stopnm, 'approaching', 0)

            final_df = pd.DataFrame(accum)
            if final_df.shape[0] != 0:
                final_df = final_df.sort_values(by='TimeDelta')
                savefile = 'Routes/'+route+'/'+normalize(dir)+'/'+normalize(stopnm)+'/'+unicode(datetime.datetime.now())+'.csv'
                final_df.to_csv(savefile, index=False)

    #clear data so it can't accidentally be processed twice
    rawfile = io.open(raw_data_path,'w')
    rawfile.close()

print '** Processing complete **'

