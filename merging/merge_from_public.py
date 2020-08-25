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
private_remote_prefix = "git@github.com:The-OpenROAD-Project-Private/"
repo_names = "OpenDB.git OpenRCX.git  TritonRoute.git OpenROAD.git OpenROAD-flow-private.git"
repo_names_master_only = "lef.git def.git OpenSTA.git flute3.git yosys.git"

print("First work on the repos with only the master branch being merged")
script_command = path_to_script + "/" + "merge_from_to_remote.py --from_remote " + github_remote_prefix + " --to_remote " + private_remote_prefix + " --repo_names " + repo_names_master_only +" --repo_branches master"
utils.run_command_locally(script_command)

print("Next work on the rest")
script_command = path_to_script + "/" + "merge_from_to_remote.py --from_remote " + github_remote_prefix + " --to_remote " + private_remote_prefix + " --repo_names " + repo_names +" --repo_branches master openroad"
utils.run_command_locally(script_command)

