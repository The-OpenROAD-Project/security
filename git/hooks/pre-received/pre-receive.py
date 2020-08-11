#!/usr/bin/env python3

import argparse
import subprocess
import shlex
import re
import sys
import os

def run_command_locally(command):
    print("command=",command)
    subprocess.run(shlex.split(command), stdout=subprocess.PIPE).stdout.decode('utf-8')

print("Running pre-commit security hook....")
# https://docs.github.com/en/enterprise/2.21/admin/policies/creating-a-pre-receive-hook-script

for line in sys.stdin: 
    if 'q' == line.rstrip(): 
        break
    print(f'Input : {line}') 
    tokens = line.split()
    oldsha = tokens[0]
    newsha = tokens[1]
    refname = tokens[2]
    print("oldsha={} newsha={} refname={}",oldsha, newsha, refname)
    print("GITHUB_PULL_REQUEST_HEAD={}",os.environ['GITHUB_PULL_REQUEST_HEAD'])
    print("GITHUB_PULL_REQUEST_BASE={}",os.environ['GITHUB_PULL_REQUEST_BASE'])
    print("GIT_DIR={}",os.environ['GIT_DIR'])
    #print(run_command_locally("git diff " + oldsha + " " + newsha))
    #print(run_command_locally("git diff " + oldsha))
    #print(run_command_locally("git diff " + newsha))
    print(run_command_locally("git show-ref " + refname))
  
print("Exit") 
exit(1)
