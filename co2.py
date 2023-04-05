#!/usr/bin/env python3
from CO2Meter import *
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import urllib.request
from requests.auth import HTTPBasicAuth
import json
sensor = CO2Meter("/dev/co2mini2")
auth_handler = urllib.request.HTTPBasicAuthHandler()
# TODO add your user and password
auth_handler.add_password(realm='solr',
                          uri='http://localhost:8983/solr/co2/update',
                          user=USER,
                          passwd=PASSWORD) 
opener = urllib.request.build_opener(auth_handler)
# ...and install it globally so it can be used with urlopen.
urllib.request.install_opener(opener)
req = urllib.request.Request("http://localhost:8983/solr/co2/update")
req.add_header('Content-Type', 'application/json; charset=utf-8')

while True:
     jsondata = json.dumps({"add":{"doc": sensor.get_data() | {'time':str(datetime.now(tz=ZoneInfo("Europe/Berlin")))}, "commitWithin": 1000}, "commit":{}})
     print(jsondata)
     jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
     req.add_header('Content-Length', len(jsondataasbytes))
     response = urllib.request.urlopen(req, jsondataasbytes)
     print("{} {} {}".format(response.status,response.msg,response.read()))
     time.sleep(60)
