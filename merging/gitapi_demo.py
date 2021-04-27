#!/usr/bin/env python3
import os
from os.path import expanduser
import urllib3
import json

user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0'}
http = urllib3.PoolManager(10, user_agent)
r = http.request("GET","https://api.github.com/repos/tspyrou/OpenROAD/commits/master/status")
print(r.data)
