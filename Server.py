import sys
sys.path.append('/usr/local/lib/python2.7/site-packages') #fix for local machine
from flask import Flask, render_template
from BusETA import DataCollection
from BusETA import Modeling
import pandas as pd
import os
import io

get_live_data = DataCollection.GetBusData.live_nearest_bus
get_model = Modeling.Persistence.get_stop_model
get_pred_input = Modeling.Persistence.get_prediction_input

def return_prediction(routename, direction, stop):
    try:
        stop_path = os.path.join('Routes', os.path.join(routename, os.path.join(direction, stop)))
        model = get_model(stop_path)

        route_dict = pd.read_csv('route_dict.csv', header=None)
        source_url = None
        for i in range(route_dict.shape[0]):
            if route_dict.ix[i,0] == routename:
                source_url = route_dict.ix[i,1]

        position_df = pd.read_csv('Routes/'+routename+'/positioning.csv', header=None)
        live_data = get_live_data(source_url, position_df, direction, stop)
        metafile = io.open(stop_path+'/model_columns.txt', 'r')
        pred_vec = get_pred_input(live_data, metafile)

        prediction = model.predict(pred_vec)
        metafile.close()  
        
        return str(prediction[0])
    except Exception as e:
        return str(e)

reload(sys)  
sys.setdefaultencoding('utf8')

ip_addr = sys.argv[1]
port = sys.argv[2]

app = Flask(__name__)

@app.route('/')
def index():
    the_routes = []
    route_names = []
    for root, dirs, files in os.walk('Routes'):
        route_names = list(dirs)
        break
    for route_dir in route_names:
        for root, dirs, files in os.walk('Routes/'+route_dir):
            route_name = os.path.basename(root)
            drs = []
            for dir in list(dirs):
                path = os.path.join(route_name,dir)
                drs.append({'name':dir,'href':path})
            the_routes.append({'name':route_name,'directions':drs})
            break
    return render_template('index.html', the_routes=the_routes)


@app.route('/<routename>/<direction>')
def route(routename, direction):
    url_path = os.path.join(routename, direction)
    full_path = os.path.join('Routes', url_path)
    the_stops = []
    stop_names = []
    for root, dirs, files in os.walk(full_path):
        stop_names = list(dirs)
        break
    for stop in stop_names:
        url = os.path.join(direction, stop)
        the_stops.append({'name':stop,'url':url})
    return render_template('stops.html', the_stops=the_stops, direction_name=direction)


@app.route('/<routename>/<direction>/<stop>')
def get_eta(routename, direction, stop):
    prediction = return_prediction(routename, direction, stop)
    return prediction

if __name__ == '__main__':
    app.run(host=ip_addr, port=port)
else:
    print 'must run directly'