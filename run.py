#run
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

cursor = DataTransforms.Transforms.cursor
prepper = DataTransforms.Transforms.prepare_dataframe
dirsplitter = DataTransforms.Transforms.split_directions
normalize = DataCollection.GetBusData.normalize
capture = DataCollection.GetBusData.capture_bus_page


def process_data():
    #fixes an encoding problem
    reload(sys)  
    sys.setdefaultencoding('utf8')

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
    return


#batch interval represents the duration for one batch of routes to be scraped continuously
#suggested batch interval = 25 min
batch_interval_minutes = float(raw_input('Enter batch interval (minutes): '))
#scrape interval represents the duration of time in between snapshots of a given route (note, this time only represents a target)
#suggested scrape interval = 20s
scrape_interval_seconds = float(raw_input('Enter scrape interval (seconds): '))
#total duration -- min
total_iterations = int(raw_input('Enter number of batch iterations: '))

BI_sec = batch_interval_minutes * 60
SI_sec = scrape_interval_seconds
print '** Commencing collection process **'

## Step 1: gather all routes from route dict, divide into batches
#### Step 1a: determine batch size
MAX_BATCH_SIZE = int(SI_sec/0.3) #determined by assuming that each scraping of a route takes ~0.25 sec, leaving 0.05 sec for error
#### Step 2a: pull route_dict into dataframe
route_dict = pd.read_csv('./route_dict.csv', header=None)
num_routes = route_dict.shape[0]
counter = num_routes # this counter is used to generate a new batch at each cycle

## Step 2: Loop through batches, passing each batch to the scrape cycler
for i in range(total_iterations):
    print i

for num in range(total_iterations):
    #generate batch by cycling thru the route_dict in intervals of BATCH_SIZE
    
    route_names = list(route_dict.ix[:,0])
    for name in route_names:
        csv = io.open('Routes/' + name + '/stopdata.csv', 'w')
        csv.write(unicode('Direction,Stop,Status,Time\n'))
        csv.close()

    batch_routes = []
    batch_size = min(MAX_BATCH_SIZE, route_dict.shape[0])
    for i in range(batch_size):
        index = counter % num_routes
        route = list(route_dict.ix[index])
        batch_routes.append(route)
        counter += 1
        
    #set the expiration timer for this batch
    batch_start_time = datetime.datetime.now()
    batch_duration = datetime.datetime.now() - batch_start_time
    while batch_duration.total_seconds() < BI_sec:
        #call the scraper on each one of the batch_routes
        scrape_start_time = datetime.datetime.now()
        for route in batch_routes:
            csv = io.open('Routes/' + route[0] + '/stopdata.csv', 'a')
            url = route[1]
            capture(csv, url)
            csv.close()
            print 'captured '+ route[0]

        scrape_duration = datetime.datetime.now() - scrape_start_time
        while scrape_duration.total_seconds() < SI_sec:
            scrape_duration = datetime.datetime.now() - scrape_start_time
        batch_duration = datetime.datetime.now() - batch_start_time
    
    print '* Batch ' + str(num) + ' complete *'
    process_data()

print '** Collection process complete **'