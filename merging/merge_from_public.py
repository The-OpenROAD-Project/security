#!/usr/bin/env python3
import sys
import subprocess
import array as arr
import os
import shlex

def run_command_locally(command):
    print("command=",command)
    retval = subprocess.run(shlex.split(command), stdout=subprocess.PIPE).stdout.decode('utf-8')
    print(retval)
    return(retval)

github_remote_prefix = "git@github.com:The-OpenROAD-Project/"
gite_remote_prefix = "git@gite.openroad.tools:The-OpenROAD-Project-Private/"
repo_names = "OpenDB.git OpenROAD.git"

work_dir = os.getcwd()
print("running in working dir ", work_dir)
path_to_script = os.path.dirname(os.path.realpath(__file__))
print("path to script=",path_to_script)

script_command = path_to_script + "/" + "merge_from_to_remote.py --from_remote " + github_remote_prefix + " --to_remote " + gite_remote_prefix + " --repo_names " + repo_names
print(run_command_locally(script_command))
