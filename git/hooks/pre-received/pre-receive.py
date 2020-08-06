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
    print("tokens[0]={}",tokens[0])
  
print("Exit") 
exit(1)
