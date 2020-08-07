#!/usr/bin/env python3

import argparse
import subprocess
import re
import sys
import os

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
    git diff old_sha new_sha
  
print("Exit") 
exit(1)
