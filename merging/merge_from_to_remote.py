#!/usr/bin/env python3
import sys
import subprocess
import array as arr
import argparse
import os
import shlex

# See for recipe to clone repo with all branches to new remote
# https://gist.github.com/niksumeiko/8972566

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def which(pgm):
    path=os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p=os.path.join(p,pgm)
        if os.path.exists(p) and os.access(p,os.X_OK):
            return p

def check_exists(pgm):
    if which(pgm) == None:
        print(pgm, "not on path")
        return False
    return True

def run_command_locally(command):
    print("command=",command)
    retval = subprocess.run(shlex.split(command), stdout=subprocess.PIPE).stdout.decode('utf-8')
    print(retval)
    if not check_exists("git"):
        exit(0)
    return(retval)

import argparse

# Parse and check arguments
parser = argparse.ArgumentParser(description='Merge all changes from a remote to a remote for a repo list')
parser.add_argument('--from_remote', dest='from_remote', action='store', help='from / source remote')
parser.add_argument('--to_remote', dest='to_remote', action='store', help='to / destination remote')
parser.add_argument('--repo_names', dest='repo_names', action='store', nargs='+', help='repo names')
parser.add_argument('--repo_branches', dest='repo_branches', action='store', nargs='+', help='repo branches to copy')

args = parser.parse_args()
from_remote_prefix = args.from_remote
to_remote_prefix = args.to_remote
repo_names = args.repo_names

repo_branches = args.repo_branches
print("from_remote_prefix=", from_remote_prefix)
print("to_remote_prefix=", to_remote_prefix)
print("repo_name=", repo_names)
print("repo_branches=", repo_branches)


work_dir = os.getcwd()
print("running in working dir ", work_dir)
print("path to script=",os.path.dirname(os.path.realpath(__file__)))
for repo in repo_names:
    print("repo=",repo)
    run_command_locally("git clone " + from_remote_prefix + repo)
    os.chdir(repo.split(".")[0])
    # fetch all branches
    run_command_locally("git fetch origin")
    branches = repo_branches
    print(branches)
    for branch in branches:
        branch = remove_prefix(branch,"remotes/origin/")
        print("working on " + branch)
        run_command_locally("git checkout -f " + branch)
        #pull from new origin gite, automatically merges
        run_command_locally("git pull origin " + branch)

    run_command_locally("git remote -v")
    run_command_locally("git remote set-url origin " + to_remote_prefix + repo)
    run_command_locally("git remote -v")
    print(run_command_locally("git push --all origin"))
    os.chdir("..")    
