#!/usr/bin/env python3
import os
import sys
import subprocess
import array as arr
import argparse
import os
import shlex
from github import Github
from os.path import expanduser

parser = argparse.ArgumentParser(description='Modify branch protection rules for admins')
parser.add_argument('--disable', default=False, dest='disable', action='store_true', help='after all changes are staged in a first run then push')
parser.add_argument('--enable', default=False, dest='enable', action='store_true', help='after all changes are staged in a first run then push')
parser.add_argument('--report_only', default=False, dest='report_only', action='store_true', help='after all changes are staged in a first run then push')

args = parser.parse_args()
enable = args.enable
disable = args.disable
report_only = args.report_only

if enable and disable:
    print("Error: both enable and disable set")
    exit

home = expanduser("~")
token_file = home + "/" + "git_merge_token"
f = open(token_file)
access_token = f.readline().strip()
f.close()

# First create a Github instance using an access token
# with needed privs
g = Github(access_token)

user = g.get_user()
print("Using token from user " + user.login)

org = g.get_organization('The-OpenROAD-Project')
print("Found organization " + org.url)

repo = org.get_repo('OpenROAD')
print("Found repo " + repo.full_name)

branches = repo.get_branches()
for branch in branches:
    if branch.name == "openroad" or branch.name == "master":
        print(branch.protection_url)
        if not report_only:
            if enable:
                branch.set_admin_enforcement()
            if disable:
                branch.remove_admin_enforcement()
        print("branch protection for admin on branch " + branch.name + " is now =",
              branch.get_protection().enforce_admins)
