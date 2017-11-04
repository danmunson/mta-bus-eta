import requests as req
import io
import pandas as pd
from bs4 import BeautifulSoup as BS
import datetime
import unicodedata
import os, shutil
import sys


class Web:

    @classmethod
    def config_web_dirs(cls, url, top_dir):
        #Goal: 
        