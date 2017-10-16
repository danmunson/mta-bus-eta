MTA Bus ETA project
The function of this project is to develop models that can accurately estimate the time until 
the next bus arrives, for each stop along a given route. Data for each stop is gathered by 
periodically scraping a webpage (see: Part I sample URLs) that gives the current position 
of all buses along the route. These models can and will be benchmarked against the MTA's 
own predictive models, which are also public. It remains to be seen who will emerge victorious...


PART I: Collecting raw data, transforming it for use in constructing models

Steps for Gathering data from MTA bus sites:
1)  Setup directory system for a route by running [config_new_route.py], and following prompts
2)  Schedule & execute a collection process by running [schedule_collection.py], and following the prompts
    (note: this will clear previous entries in the stopdata.csv file)
3)  Process all collected data into a format useful for Bus ETA prediction models by running [process.py]

NOTE--> Important assumptions in data collection process:
    a. No two buses will ever occupy the same stop position
    b. 3 buses will never be at 3 adjacent stops simultaneously
    c. In each successive "snapshot" the bus must be in the same position as the previous, or the next position

SAMPLE URLS:
M60SBS route: https://bustime.mta.info/m/?q=M60-SBS
M15 route: https://bustime.mta.info/m/?q=M15

DEPENDENCIES:
requests (pip install requests)
BeautifulSoup4 (pip install bs4)
lxml (pip install lxml)