#!/usr/bin/env python3
import os
from os.path import expanduser
import urllib3
import json


http = urllib3.PoolManager()
r = http.request("GET","https://api.github.com/repos/tspyrou/OpenROAD/commits/master/status")
print(r.data)
