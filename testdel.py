#test script for deleting old files
import sys
import os
import datetime as dt

MAX_DAYS = 21

for r, ds, fs in os.walk('Routes'):
    for f in fs:
        name, ext = os.path.splitext(f)
        if ext == '.csv':
            if name == 'stopdata' or name == 'positioning':
                continue
            timestamp = dt.datetime.strptime(name, '%Y-%m-%d %H:%M:%S.%f')
            delta = dt.datetime.now() - timestamp
            if delta.total_seconds() > (24 * 60 * 60 * MAX_DAYS):
                pathname = name + ext
                os.remove(pathname)