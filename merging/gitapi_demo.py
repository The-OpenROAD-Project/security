#!/usr/bin/env python3
import requests
import os
from pprint import pprint

token = os.getenv('GITHUB_TOKEN', '...')
headers = {'Authorization': f'token {token}'}

owner = "The-OpenROAD-Project-private"
repo = "OpenROAD"
query_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
params = {
    "state": "open",
}
r = requests.get(query_url, headers=headers, params=params)
pprint(len(r.json()))


query_url = f"https://api.github.com/repos/{owner}/{repo}/branches"
params = {
}

r = requests.get(query_url, headers=headers, params=params)
pprint(len(r.json()))

