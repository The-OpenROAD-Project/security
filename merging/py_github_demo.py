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


