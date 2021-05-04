#!/usr/bin/env python3
import requests
import os
from pprint import pprint
import simplejson
import argparse


# Parse and check arguments
parser = argparse.ArgumentParser(description='Push labeled branch to a new project')
parser.add_argument('--from_remote', dest='from_remote', action='store', help='from / source remote')
parser.add_argument('--to_remote', dest='to_remote', action='store', help='to / destination remote')
parser.add_argument('--repo_name', dest='repo_name', action='store', help='repo name')
parser.add_argument('--repo_branch', dest='repo_branch', action='store', help='repo branch to push')

args = parser.parse_args()
from_remote_prefix = args.from_remote
to_remote_prefix = args.to_remote
repo_name = args.repo_name
repo_branch = args.repo_branch


def process_one_repo(token, owner, staging, repo):
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

process_one_repo(token, from_remote_prefix ,to_remote_prefix, repo_name)
#./push_labeled_branches_to_staging.py --from_remote The-OpenROAD-Project-private --to_remote The-OpenROAD-Project-staging --repo_name OpenROAD --repo_branch test
