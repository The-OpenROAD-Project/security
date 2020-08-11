#!/usr/bin/env python3
import sys
import subprocess
import array as arr
import argparse
import os
import shlex

def which(pgm):
    path=os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p=os.path.join(p,pgm)
        if os.path.exists(p) and os.access(p,os.X_OK):
            return p

def check_exists(pgm):
    if which(pgm) == None:
        print(pgm, "not on path")


def run_command_locally(command):
    print("command=",command)
    print(subprocess.run(shlex.split(command), stdout=subprocess.PIPE).stdout.decode('utf-8'))

github_remote_prefix = "git@github.com:The-OpenROAD-Project/"
gite_remote_prefix = "git@gite.openroad.tools:The-OpenROAD-Project-Private/"
repo_names = [
    "OpenROAD.git",
    "OpenROAD-flow.git",
    "TritonRoute.git"
    ]
work_dir = os.getcwd()
print("running in working dir ", work_dir)
print("path to script=",os.path.dirname(os.path.realpath(__file__)))

run_command_locally("git clone --branch openroad " + github_remote_prefix + "OpenROAD.git")
os.chdir("OpenROAD")
#origin remote is github
run_command_locally("git remote -v")
run_command_locally("git remote add gite " + gite_remote_prefix + "OpenROAD.git")
#gite remote is gite.openroad.tools
run_command_locally("git remote -v")
run_command_locally("git pull gite openroad")

#copy to new remote for first time
#git remote rename origin github_origin
#git remote add origin git@gite.openroad.tools:The-OpenROAD-Project-Private/OpenROAD.git
#git push origin master


