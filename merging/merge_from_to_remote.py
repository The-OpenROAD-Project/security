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
args = parser.parse_args()
from_remote_prefix = args.from_remote
to_remote_prefix = args.to_remote
repo_names = args.repo_names
print("from_remote_prefix=", from_remote_prefix)
print("to_remote_prefix=", to_remote_prefix)
print("repo_name=", repo_names)

#repo_names = [
#    "OpenDB.git",
#    "OpenROAD.git",
#    "OpenROAD-flow.git",
#    "TritonRoute.git"
#    ]

work_dir = os.getcwd()
print("running in working dir ", work_dir)
print("path to script=",os.path.dirname(os.path.realpath(__file__)))
for repo in repo_names:
    print("repo=",repo)
    run_command_locally("git clone " + from_remote_prefix + repo)
    os.chdir(repo.split(".")[0])
    # fetch all branches
    run_command_locally("git fetch origin")
    branches_raw_nosplit = run_command_locally("git branch -a")
    # First line is * master, second line is pointer to master remote skip them
    #* master
    #remotes/origin/HEAD -> origin/master
    branches_raw_split = branches_raw_nosplit.split("\n")[2:-1]
    branches = [item.strip() for item in branches_raw_split]
    print(branches)
    for branch in branches:
        branch = remove_prefix(branch,"remotes/origin/")
        print("working on " + branch)
        run_command_locally("git checkout -f " + branch)
        #pull from new origin gite, automatically merges
        run_command_locally("git pull origin " + branch)

    #origin remote is github
    run_command_locally("git remote -v")

    #change origin to gite
    run_command_locally("git remote set-url origin " + to_remote_prefix + repo)

    #remote is gite.openroad.tools
    run_command_locally("git remote -v")

    #push to origin which is gite
    print(run_command_locally("git push --all origin"))
    os.chdir("..")    
