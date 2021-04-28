#!/usr/bin/env python3
import requests
import os
from pprint import pprint

token = os.getenv('GITHUB_TOKEN', '...')
owner = "tspyrou"
repo = "OpenROAD"
query_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
params = {
    "state": "open",
}
headers = {'Authorization': f'token {token}'}
r = requests.get(query_url, headers=headers, params=params)
pprint(r.json())

