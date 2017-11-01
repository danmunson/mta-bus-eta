import sys
sys.path.append('/usr/local/lib/python2.7/site-packages') #fix for local machine

from flask import Flask
import BusETA

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello'


if __name__ == '__main__':
    app.run()
else:
    print 'must run directly'