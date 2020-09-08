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

hooks = utils.run_command_locally("git config --get core.hooksPath")

for repo in repo_names:
    utils.run_command_locally("git clone " + from_remote_prefix + repo)
    os.chdir(repo.split(".")[0])
    # fetch all branches
    utils.run_command_locally("git pull")
    # origin is the from_remote, dest is the to remote
    utils.run_command_locally("git remote add dest " + to_remote_prefix + repo)
    branches = repo_branches
    for branch in branches:
        branch = utils.remove_prefix(branch, "remotes/origin/")
        utils.run_command_locally("git checkout -f " + branch)
        utils.run_command_locally("{}/pre-commit.py --local".format(hooks))
        # pull from new origin gite, automatically merges
        utils.run_command_locally("git pull dest " + branch)
        utils.run_command_locally("git pull origin " + branch)

    utils.run_command_locally("git remote -v")
    utils.run_command_locally("git push --all dest")
    os.chdir("..")    
