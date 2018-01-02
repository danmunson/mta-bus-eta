import io, os, shutil, unicodedata, datetime
from BusETA import Modeling as Md
from BusETA import Algorithms

MODEL_OBJ = Algorithms.MedianLookup
def train_new_models():
    route_names = []
    for root, ds, fs in os.walk('Routes'):
        route_names = list(ds)
        break
    for route in route_names:
        stopdfs = Md.Read.read_all_stops(route)
        finished_dfs = Md.FeatureEng.apply_SDT(stopdfs)
        Md.Persistence.train_save_route(finished_dfs, MODEL_OBJ)
    return

train_new_models()