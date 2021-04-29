#!/usr/bin/env python3
import requests
import os
from pprint import pprint
import simplejson

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
c = r.content
j = simplejson.loads(c)
for item in j:
    print(item["name"])


query_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
params = {
    "state": "open",
}
r = requests.get(query_url, headers=headers, params=params)
pprint(len(r.json()))
c = r.content
j = simplejson.loads(c)
#print(j[0])
for item in j:
    labels = item["labels"]
    if len(labels) > 0:
        print("url", item["url"], " labels ", labels, " title ", item["title"], " source branch ", item["head"]["ref"])
        for label in labels:
            print(label["name"])
        
