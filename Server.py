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
get_lm_pred_input = Modeling.Persistence.get_lm_prediction_input
get_categ_pred_input = Modeling.Persistence.get_categ_prediction_input

def return_prediction(routename, direction, stop, current_model_type):
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

        if live_data['postat'] == 'XXXX':   #indicates there are not enough earlier stops to make a prediction
            return 'No nearby buses. Try again soon.'
        
        pred_vec = None
        pred_dict = None
        prediction = None

        if current_model_type == 'lm':
            metafile = io.open(stop_path+'/model_columns.txt', 'r')
            pred_vec, pred_dict, postat_bool = get_lm_pred_input(live_data, metafile)
            metafile.close()
            if not postat_bool:
                return 'Bus out of range. Try again soon.'
            else:
                prediction = model.preddict(pred_vec)
        elif current_model_type == 'categ':
            try:
                pred_vec = get_categ_pred_input(live_data)
                prediction = model.predict(pred_vec)
            except Exception as e:
                return 'Bus out of range. Try again soon.'
        
        est_mins = round(prediction[0]/60, 1)
        return str(mins) + ' minutes.'
    except Exception as e:
        return str(e)

reload(sys)  
sys.setdefaultencoding('utf8')

ip_addr = sys.argv[1]
port = sys.argv[2]
current_model_type = sys.argv[3]    #sad, sorry shortcut

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


@app.route('/<routename>/eta/<direction>/<stop>')
def get_eta(routename, direction, stop):
    prediction = return_prediction(routename, direction, stop, current_model_type)
    return prediction

if __name__ == '__main__':
    app.run(host=ip_addr, port=port)
else:
    print 'must run directly'