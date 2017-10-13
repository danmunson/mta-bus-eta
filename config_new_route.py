import requests as req
import io
import pandas as pd
from bs4 import BeautifulSoup as BS
import datetime
import unicodedata
import os, shutil
from BusETA import DataTransforms
from BusETA import DataCollection

directory_setup = DataCollection.GetBusData.setup_directories
route_dict = open('./route_dict.csv', 'a')

route_name = raw_input('Enter route name: ')
route_url = raw_input('Enter route URL: ')

route_dir = 'Routes/'+route_name
directory_setup(route_url, route_dir)

new_line = route_name + ',' + route_url + '\n'
route_dict.write(new_line)
route_dict.close()

print '** Configuration complete **'