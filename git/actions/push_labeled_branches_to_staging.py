#!/usr/bin/env python3
import requests
import os
from pprint import pprint
import simplejson



def process_one_repo(token, owner,staging,repo):
    print("Processing " + owner + " " + staging)
    query_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    params = {
        "state": "open",
    }
    r = requests.get(query_url, headers=headers, params=params)
    c = r.content
    j = simplejson.loads(c)
    for item in j:
        labels = item["labels"]
        if len(labels) > 0:
            for label in labels:
                source_branch = item["head"]["ref"]
                dest_branch = item["base"]["ref"]
                label_name = label["name"]
                if label_name == "Ready To Sync Public":
                    print("Branch " + source_branch + " is ready to push to staging. Targeted to merge to " + dest_branch + ".")
        

token = os.getenv('GITHUB_TOKEN', '...')
headers = {'Authorization': f'token {token}'}
staging = "The-OpenROAD-Project-staging"
owner = "The-OpenROAD-Project-private"
repos = ["OpenROAD", "OpenROAD-flow-scripts"]
for repo in repos :
    process_one_repo(token, owner,staging,repo)
