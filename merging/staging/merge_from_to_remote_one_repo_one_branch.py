#!/usr/bin/env python3
import sys
import subprocess
import array as arr
import argparse
import os
import shlex

# See for recipe to clone repo with all branches to new remote
# https://gist.github.com/niksumeiko/8972566

work_dir = os.getcwd()
path_to_script = os.path.dirname(os.path.realpath(__file__))
sys.path.append(path_to_script)
import utils

# find path to precommit script
path_to_pre_commit = os.path.split(path_to_script)[0]
path_to_pre_commit = os.path.split(path_to_pre_commit)[0]
path_to_pre_commit = path_to_pre_commit + "/git/hooks/pre-commit.py"
print(path_to_pre_commit)

# Parse and check arguments
parser = argparse.ArgumentParser(description='Merge all changes from a remote to a remote for a repo list')
parser.add_argument('--from_remote', dest='from_remote', action='store', help='from / source remote')
parser.add_argument('--to_remote', dest='to_remote', action='store', help='to / destination remote')
parser.add_argument('--repo_name', dest='repo_name', action='store', help='repo name')
parser.add_argument('--repo_branch', dest='repo_branch', action='store', help='repo branch to merge')
parser.add_argument('--push', default=False, dest='push', action='store_true', help='after all changes are staged in a first run then push')

args = parser.parse_args()
from_remote_prefix = args.from_remote
to_remote_prefix = args.to_remote
repo_name = args.repo_name
push = args.push
repo_branch = args.repo_branch

hooks = utils.run_command_locally("git config --get core.hooksPath").rstrip()

# setup open file to put diffs into for review
file_name = "diffs-from-" + from_remote_prefix + "-to-" + to_remote_prefix + "-branch-" + repo_branch
file_name = file_name.replace("/","")
file_name = file_name.replace("\\","")
if os.path.exists(file_name):
    append_write = 'a'
else:
    append_write = 'w'


# clone and setup destination remote
utils.run_command_locally("git clone " + from_remote_prefix + repo_name)
os.chdir(repo_name.split(".")[0])

# origin is the from_remote, dest is the to remote
utils.run_command_locally("git remote add dest " + to_remote_prefix + repo_name)
#utils.run_command_locally("git fetch dest " + repo_branch)

# switch to branch
utils.run_command_locally("git switch " + repo_branch)
utils.run_command_locally("git status")

# print remotes for log
utils.run_command_locally("git remote -v")

# Run security check
print("running pre-commit.py --local")
retval = utils.run_command_locally(path_to_pre_commit + " --local")
print("retval={}".format(retval))

# push to destination remote
if push:
    utils.run_command_locally("git push dest")
    utils.run_command_locally("git status")
os.chdir("..")

