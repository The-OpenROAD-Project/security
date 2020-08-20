#!/usr/bin/env python3
import sys
import subprocess
import array as arr
import os
import shlex

work_dir = os.getcwd()
path_to_script = os.path.dirname(os.path.realpath(__file__))
sys.path.append(path_to_script)
import utils

github_remote_prefix = "git@github.com:The-OpenROAD-Project/"
gite_remote_prefix = "git@github.com:The-OpenROAD-Project-Private/"
repo_names = "OpenDB.git OpenROAD.git"

script_command = path_to_script + "/" + "merge_from_to_remote.py --to_remote " + github_remote_prefix + " --from_remote " + gite_remote_prefix + " --repo_names " + repo_names +" --repo_branches master openroad"
run_command_locally(script_command)
