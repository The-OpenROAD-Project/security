#!/usr/bin/env python3
import sys
import subprocess
import array as arr
import os
import shlex
import argparse

work_dir = os.getcwd()
path_to_script = os.path.dirname(os.path.realpath(__file__))
sys.path.append(path_to_script)
import utils

# Parse and check arguments
parser = argparse.ArgumentParser(description='Merge all changes from a remote to a remote for a repo list')
parser.add_argument('--push', default=False, dest='push', action='store_true', help='after all changes are staged in a first run then push')

args = parser.parse_args()
push = args.push
print("push=",push)

github_remote_prefix = "git@github.com:The-OpenROAD-Project/"
private_remote_prefix = "git@github.com:The-OpenROAD-Project-Private/"
repo_names = ""
repo_names_master_only = "OpenROAD.git OpenROAD-flow-scripts.git"

script_command = path_to_script + "/" + "merge_from_to_remote.py" + " --to_remote " + github_remote_prefix + " --from_remote " + private_remote_prefix + " --repo_names " + repo_names_master_only + " --repo_branches master"
if push:
    script_command = script_command + " --push"
print(script_command)
utils.run_command_locally(script_command)

