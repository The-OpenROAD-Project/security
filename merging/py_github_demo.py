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

org = g.get_organization('The-OpenROAD-Project-private')
print(org.url)

repo = org.get_repo('OpenROAD')
print(repo.full_name)

branches = repo.get_branches()
for branch in branches:
    if branch.name == "master":
        print(branch.name)
        print(branch.protection_url)
        print(branch.get_protection().enforce_admins)
        print(branch.remove_admin_enforcement())
        print(branch.get_protection().enforce_admins)
        print(branch.set_admin_enforcement())
        print(branch.get_protection().enforce_admins)
        print(branch.get_required_status_checks())

        
pulls = repo.get_pulls(state="open")
for pull in pulls:
    title = pull.title
    base = pull.base #base.ref is the branch being merged into .label is the repo
    head = pull.head #head.ref is the branch with the new code .label is the repo
    number = pull.number
    merged = pull.merged # skip for sync
    mergeable = pull.mergeable # no merge conflict
    mergeable_state = pull.mergeable_state # tests ok, green button ready (may not work when master protected)
    user = pull.user
    state = pull.state
    milestone = pull.milestone
    review_comment_url = pull.review_comment_url
    draft = pull.draft
    update_branch = pull.update_branch()
    labels = pull.labels
    print("{} {} {} {} {} {} {} {} {} {} {} {} {} {} {}".format(number,base, merged,mergeable,mergeable_state,user, state, milestone, draft, update_branch, labels, base.label, base.ref, head.label, head.ref))
    for l in labels:
        print("l={} {}".format(l.name, l.name == "Ready To Sync Public"))
          
    


