import pandas as pd
import os

position_df = pd.read_csv('Routes/M60SBS/positioning.csv', header=None)
ord_stops = list(position_df.ix[:,0])

reg_stops = []
for r, d, f in os.walk('Routes/M60SBS'):
    reg_stops = list(d)
    break

for stop in ord_stops:
    tf = (stop in reg_stops)
    print tf, ' : ', stop
