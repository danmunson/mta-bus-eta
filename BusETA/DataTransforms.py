# for transforming raw data from the mta bus status websites into usable data for building models
import io
import pandas as pd
import datetime
import os, shutil
import unicodedata
from random import *

class Transforms:

    #Traverse down (forwards in time) the dataframe, searching for observations of "approaching" for a given stop
    #When finding the aforementioned case, the collector() is called to interpret and gather data relative to this point
    #After that process, it is important to skip past any successive 'snapshots' of the same bus in the same position --> hence, use of 'jump_size'
    @classmethod
    def cursor(cls, full_df, obs_df, stop_name, desired_status, row_index):
        try:
            row = list(full_df.ix[row_index])
            if row[1] == stop_name and (row[2] == desired_status):
                timestamp = row[3]
                position = row[4]
                situation = cls.get_initial_situation(full_df, timestamp, row[0], int(position))
                cls.collector(full_df, obs_df, row_index-1, timestamp, timestamp, position, situation)
                jump_size = cls.jump_size(full_df, stop_name, desired_status, row_index)
                cls.cursor(full_df, obs_df, stop_name, desired_status, row_index+jump_size) 
            else:
                cls.cursor(full_df, obs_df, stop_name, desired_status, row_index+1) 
        except Exception as e:
            pass
            #print 'Cursor failed at row ' + str(row_index)
            #print e
        return
    
    #The purpose of this function is to enable the cursor to skip past any 'duplicates', or successive snapshots of
    #the same bus in the same position
    @classmethod
    def jump_size(cls, full_df, stop_name, status, row_index):
        try:
            row = list(full_df.ix[row_index])
            orig_time = row[3]
            
            found = False
            count = 1
            while not found:
                new_row = list(full_df.ix[row_index+count])
                new_time = new_row[3]
                if orig_time == new_time:
                    count += 1
                    continue
                timeblock = full_df[full_df.ix[:,'Time'] == new_time]
                subdf = timeblock[timeblock.ix[:,'Stop'] == stop_name]
                subdf = subdf[subdf.ix[:,'Status'] == status]
                if subdf.shape[0] > 0: #if this is the case, then this is a snapshot of the same bus in the same position
                    count += 1
                    continue
                else:
                    found = True
            return count
        except:
            return 1

    #Traverse up (backwards in time) the dataframe, searching for observations of the same bus at earlier points in time;
    # will stop after 20min of elapsed time
    @classmethod
    def collector(cls, full_df, obs_df, row_index, ignore_timestamp, orig_timestamp, prev_collected_pos, prev_situation):
        MAX_TIME_DIFF = 60*20 #20 minutes
        try:
            row = list(full_df.ix[row_index])
            timestamp = row[3]
            if timestamp == ignore_timestamp:
                cls.collector(full_df, obs_df, row_index-1, timestamp, orig_timestamp, prev_collected_pos, prev_situation)
                return
            timediff = orig_timestamp-timestamp
            if timediff.total_seconds() > MAX_TIME_DIFF:
                return

            obs_situation, obs_stop_pos, obs_status = cls.getObservationFromBlock(full_df, timestamp, prev_collected_pos, prev_situation)
            
            if obs_stop_pos == None:
                return
            #defining format of obs_df
            this_obs = {'Position':obs_stop_pos, 'Status':obs_status, 'Timestamp':timestamp, 'TimeDelta':timediff.total_seconds()}
            obs_df.append(this_obs)
            cls.collector(full_df, obs_df, row_index-1, timestamp, orig_timestamp, obs_stop_pos, obs_situation)        
        except Exception as e:
            pass
            #print 'Collector failed at row ' + str(row_index)
            #print e
        return

    @classmethod
    def getObservationFromBlock(cls, full_df, timestamp, prev_collected_pos, prev_situation):

        block = full_df[full_df.ix[:,3] == timestamp]
        block = block.reset_index(drop=True)
        blocklen = (block.shape)[0]
        position = {'prev':False, 'same':False, 'next':False}
        index = {'prev':None, 'same':None, 'next':None}
        
        #get relative-local stop occupancy in adjascent stops
        for i in range(int(blocklen)):
            row = block.ix[i]
            pos = row[4]
            if pos == prev_collected_pos:
                position['same'] = True
                index['same'] = i
            elif int(prev_collected_pos) > 0 and int(pos) == int(prev_collected_pos)-1:
                position['prev'] = True
                index['prev'] = i
            elif int(pos) == int(prev_collected_pos)+1:
                position['next'] = True
                index['next'] = i
        ##
        ind, this_situation = cls.assess_situation(position, index, prev_situation)
        ##
        bus_row = list(block.ix[ind])
        stop_pos = bus_row[4]
        status = bus_row[2]

        return this_situation, stop_pos, status
        
    @classmethod
    def assess_situation(cls, position, index, prev_situation):
        situation = None
        ind = None
        #determine which observation was the appropriate bus
        if prev_situation == 'A' or prev_situation == 'C':
            if position['same']:
                ind = index['same']
            elif position['prev']:
                ind = index['prev']
        elif prev_situation == 'B':
            if position['prev']:
                ind = index['prev']
            elif position['same']:
                ind = index['same']
        #determine which class the current situation is
        if position['same'] and position['next']:
            situation = 'B'
        elif position['same'] and position['prev']:
            situation = 'C'
        else:
            situation = 'A'

        return ind, situation

    @classmethod
    def get_initial_situation(cls, df, time, direction, position):
        situation = 'A'
        sub_df = df[df['Time'] == time]
        sub_df =sub_df[sub_df['Direction'] == direction]
        positions = sub_df.ix[:,4]
        for i in positions:
            i = int(i)
        #get current situation
        if (position-1) in positions:
            situation = 'C'
        elif (position+1) in positions:
            situation = 'B'
        return situation

    @classmethod
    def prepare_dataframe(cls, observation_csv, orderdf):
        obs = pd.read_csv(observation_csv, header=0)
        positions = []
        for i in range(len(obs.index)):
            row = list(obs.ix[i])
            direction = row[0]
            stop = row[1]
            position = cls.get_stop_position(direction, stop, orderdf)
            positions.append(position)
        pos_series = pd.Series(positions)
        #add stop positions to obs dataframe
        new_obs = pd.concat([obs, pos_series], axis = 1)
        return new_obs

    @classmethod
    def get_stop_position(cls, direction, stop, orderdf):
        for i in range(len(orderdf.index)):
            row = list(orderdf.ix[i])
            if row[0] == direction and row[1] == stop:
                return row[2]

    @classmethod
    def split_directions(cls, df, status):
        dir_names = list(set(list(df.ix[:,0])))
        directions = []
        stops = []
        for name in dir_names:
            dfi = df[df.ix[:,'Direction'] == name]
            dfi = dfi.reset_index(drop=True)
            dfi.ix[:,'Time'] = pd.to_datetime(dfi.ix[:,'Time'], format='%Y-%m-%d %H:%M:%S.%f')
            dfi.sort_values(by='Time', ascending=True)
            directions.append(dfi)
            # purpose: have stop_list only contain names of stops that have had a status of 'approaching'
            dfi_ = dfi[dfi.ix[:,'Status'] ==  status]
            stop_list = list(set(list(dfi_.ix[:,1])))
            stops.append(stop_list)
        return directions, stops


