#!/usr/bin/env python3
import os
from github import Github


from os.path import expanduser
home = expanduser("~")
token_file = home + "/" + "git_merge_token"
f = open(token_file)
access_token = f.readline().strip()
f.close()

# First create a Github instance using an access token
# with needed privs
g = Github(access_token)

user = g.get_user()
print(user.login)
print(user.name)

org = g.get_organization('The-OpenROAD-Project')
print(org.url)

repo = org.get_repo('OpenROAD')
print(repo.full_name)

branches = repo.get_branches()
for branch in branches:
    if branch.name == "openroad":
        print(branch.name)
        print(branch.protection_url)
        print(branch.get_protection().enforce_admins)
        print(branch.remove_admin_enforcement())
        print(branch.get_protection().enforce_admins)
        print(branch.set_admin_enforcement())
        print(branch.get_protection().enforce_admins)


