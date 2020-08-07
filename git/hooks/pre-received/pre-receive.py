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
  
for line in sys.stdin: 
    if 'q' == line.rstrip(): 
        break
    print(f'Input : {line}') 
    tokens = line.split()
    oldsha = tokens[0]
    newsha = tokens[1]
    refname = tokens[2]
    print("oldsha={} newsha={} refname={}",oldsha, newsha, refname)
    print(run_command_locally("git diff " + oldsha + " " + newsha))
  
print("Exit") 
exit(1)
