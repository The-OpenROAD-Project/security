#!/usr/bin/env python3

import argparse
import subprocess
import re
import sys
import os

print("Running pre-commit security hook....")import sys 
  
for line in sys.stdin: 
    if 'q' == line.rstrip(): 
        break
    print(f'Input : {line}') 
  
print("Exit") 
