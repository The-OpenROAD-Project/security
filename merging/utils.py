import sys
import subprocess
import array as arr
import argparse
import os
import shlex

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def which(pgm):
    path=os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p=os.path.join(p,pgm)
        if os.path.exists(p) and os.access(p,os.X_OK):
            return p

def check_exists(pgm):
    if which(pgm) == None:
        print(pgm, "not on path")
        return False
    return True

def run_command_locally(command):
    retval = ""
    try:
        retval = subprocess.check_output(shlex.split(command)).decode('utf-8')
    except subprocess.CalledProcessError as exc:
        print("error code ", exc.returncode, " ", exc.output)
    return(retval)

