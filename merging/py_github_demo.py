#!/usr/bin/env python3
from github import Github

# First create a Github instance:

# using username and password
# g = Github("user", "password")

f = open('/home/tspyrou/git_merge_token')
access_token = f.readline().strip()
f.close()

# or using an access token
g = Github(access_token)

user = g.get_user()
print(user.login)
print(user.name)


# Github Enterprise with custom hostname
#g = Github(base_url="https://{hostname}/api/v3", login_or_token="access_token")

# Then play with your Github objects:
for repo in g.get_user().get_repos():
    print(repo.name)
    print(repo.full_name)
