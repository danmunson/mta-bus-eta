Steps for Gathering data from MTA bus sites:
1)  Setup directory system for a route by running [config_new_route.py], and following prompts
2)  Schedule & execute a collection process by running [schedule_collection.py], and following the prompts
    (note: this will clear previous entries in the stopdata.csv file)
3)  Process all collected data into a format useful for Bus ETA prediction models by running [process.py]

NOTE--> Important assumptions in data collection process:
    a. No two buses will ever occupy the same stop position
    b. 3 buses will never be at 3 adjacent stops simultaneously
    c. In each successive "snapshot" the bus must be in the same position as the previous, or the next position

NOTE--> After building a model (module coming soon), predicted ETAs can be compared against MTA's provided ETAs (found by clicking link on bus stop name)


SAMPLE URLS:
M60SBS route: https://bustime.mta.info/m/?q=M60-SBS
M15 route: https://bustime.mta.info/m/?q=M15

DEPENDENCIES:
requests (pip install requests)
BeautifulSoup4 (pip install bs4)
lxml (pip install lxml)