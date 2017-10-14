import requests as req
import io
import pandas as pd
from bs4 import BeautifulSoup as BS
import datetime
import unicodedata
import os, shutil
import sys

class GetBusData:

    @classmethod
    def setup_directories(cls, url, top_dir):
        page = req.get(url)
        html = page.text
        soup = BS(html, 'lxml')
        directions = soup.find_all(class_='directionForRoute')

        for direction in directions:
            dir_name = cls.normalize(direction.contents[0].string)
            os.makedirs(top_dir + '/' + dir_name)

            stops = direction.contents[1].contents

            for position in range(len(stops)):
                stop_name = stops[position].a.string
                stop_name = cls.normalize(stop_name)
                os.makedirs(top_dir + '/' + dir_name + '/' + stop_name)

        position_loc = top_dir + '/' + 'positioning.csv'
        cls.get_stop_positions(soup, position_loc)
        return

    @classmethod
    def normalize(cls, route_name):
        chars = list(unicode(route_name))
        new_chars = []
        for char in chars:
            try:
                if char == '/':
                    char = '__'
                    new_chars.append(char)
                else:
                    new_chars.append(char)
            except:
                new_chars.append('__')
        string = unicode('')
        for char in new_chars:
            string = string + unicode(char)
        return string

    @classmethod
    def get_stop_positions(cls, soup, writefile):
        stop_orders = pd.DataFrame()
        directions = soup.find_all(class_='directionForRoute')
        for direction in directions:
            dir_name = direction.contents[0].string
            stops = direction.contents[1].contents
            for position in range(len(stops)):
                stop_name = stops[position].a.string
                row = pd.Series([dir_name, stop_name, int(position)])
                stop_orders = stop_orders.append(row, ignore_index=True)
        
        stop_orders.to_csv(writefile, header=None, encoding='utf-8', index=False)
        return

    @classmethod
    def get_stop_data(cls, obs_file, pos_file, url, interval, iterations):
        cls.get_stop_positions(url, pos_file)
        cls.run_loop(interval, iterations, obs_file, url)
        return

    @classmethod
    def save_stop(cls, data, string):
        line = data['direction'] + ',' + data['stop'] + ',' + data['status'] + ',' + data['time'] + '\n'
        string = string + line
        return string

    @classmethod
    def get_direction_title(cls,stop):
        direction = stop.parent.parent.parent.parent.previous_sibling.string
        return direction
    
    @classmethod
    def capture_bus_page(cls, csv, url):
        page = req.get(url)
        html = page.text
        time = str(datetime.datetime.now())
        soup = BS(html, 'lxml')
        bolds = soup.find_all('strong')
        stop_line = ''
        active = {}
        for i in range(len(bolds)):
            stop = bolds[i]
            try:
                ch_name = stop.contents[0].name
                par_name = stop.parent.name
                if ch_name == 'a' and par_name == 'li': #then assume it represents the bolded stop name, and a status will be the next element
                    name = stop.contents[0].string
                    active['stop'] = name
                    status = bolds[i+1].string
                    ## fix for error on Linux version of BS4 (cannot pick up "< 1 stop away", probably due to "<" char)
                    if status == None:
                        status = '< 1 stop away'
                    ##
                    active['status'] = status
                    active['time'] = time
                    active['direction'] = cls.get_direction_title(bolds[i+1])
                    stop_line = cls.save_stop(active, stop_line)
                    active = {}
            except:
                continue
        csv.write(unicode(stop_line))
        return
