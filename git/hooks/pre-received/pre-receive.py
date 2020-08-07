#!/usr/bin/env python3

import argparse
import subprocess
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
    run_command_locally("git diff " + old_sha + " " + new_sha)
  
print("Exit") 
exit(1)
