#!/usr/bin/env python3

import argparse
import subprocess
import re
import sys
import os

print("Running pre-commit security hook....")

# Limits for rules
file_add_limit    = 10
file_change_limit = 50

# The following patterns are regular expressions and are matched
# case-insensitive.  They are matched anywhere with the string
# and can have leading or trailing characters and still match.

# Blocked paths (unless allowed below).
blocked_path_patterns = [
    r"flow/",
    r"\.gds",
    r"\.lef",
    r"\.cdl",
    r"\.cal",
    r"\.v",
    r"\.db",
    r"\.lib",
    r"tsmc",
    r"gf\d+",
    r"\d+lp",  # Invecus
    r"sc\d+",  # ARM-style names
]

# Allowed paths are exceptions to blocked paths above.
allowed_path_patterns = [
    r"^flow/designs",
    r"^flow/docs",
    r"^flow/platforms/nangate45",
    r"^flow/platforms/sky130",
    r"^flow/scripts",
    r"^flow/test",
    r"^flow/util",
]

# Files may not contain these patterns in their content anywhere (not
# just the changed portion).  All staged files are checked, even
# "allowed" files - there should still be no bad content in allowed
# files.
block_content_patterns = [
    r"gf\d+",    # eg gf12, gf14
    r"tsmc",     # eg tsmc65lp
    r"\d+lp",    # eg 12LP (for Invecus)
    r"\barm\b",  # eg ARM
]


def error(msg):
    msg = '\n\nERROR: {}\n\nTo request an exception please contact Tom' \
      .format(msg)
    sys.exit(msg)


def run_command(command):
    r = subprocess.run(command,
                       stdout=subprocess.PIPE,
                       encoding='utf-8',
                       shell=True)
    r.check_returncode()

    # Split the output into lines
    return r.stdout.rstrip().split('\n')


def check_content(name):
    # the : in front of the file name gets the staged version of the
    # file, not what is currently on disk unstaged which could be
    # different (and possibly not contain the keyword).  We check the
    # whole file not just the changed portion.
    lines = run_command('git show :{}'.format(name))
    for cnt, line in enumerate(lines):
        for pattern in block_content_patterns:
            # re.search matches anywhere in the line
            if re.search(pattern, line, re.IGNORECASE):
                msg = "File {} contains blocked content pattern" \
                  " \"{}\" on line {} :\n  {}" \
                  .format(name,
                          pattern,
                          cnt + 1,
                          line)
                error(msg)


def is_blocked(name, args):
    'Is this name blocked by the path patterns?'
    blocked = False
    for pattern in blocked_path_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            blocked = True
            if args.verbose:
                print("{} matches blocked {}".format(name, pattern))
            break
    if blocked:
        for pattern in allowed_path_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                blocked = False
                if args.verbose:
                    print("{} matches allowed {}".format(name, pattern))
                break
    return blocked


def parse_args(args):
    parser = argparse.ArgumentParser(description='Commit checker')
    parser.add_argument('--report', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    return parser.parse_args(args)


def main(args=None):
    # Make sure this is running from the top level of the repo
    try:
        top = run_command('git rev-parse --show-toplevel')[0]
    except:
        error('Not running in git repo: {}'.format(os.getcwd()))

    # Make sure we are running from the root (always true as a hook
    # but not if run manually)
    if os.getcwd() != top:
        print('Running from {}'.format(top))
        os.chdir(top)

    # Get status of the staged files
    lines = run_command('git diff --cached --name-status')
    if len(lines[0]) == 0:
        sys.exit('ERROR: Nothing is staged')

    # Split the lines in status & file.  Filenames containing whitespace
    # are problematic so don't do that.
    lines = [l.split() for l in lines]
    for l in lines:
        assert(len(l) == 2)     # sanity check : <status> <file>
        assert(len(l[0]) == 1)  # sanity check : <status> is one char

    # Newly added files
    added = [f[1] for f in lines if f[0] == 'A']
    num_added = len(added)

    # This is all other changes, including modify, rename, copy, delete
    num_changed = len(lines) - num_added

    if (args.report):
        print("Added {} (limit: {})".format(num_added, file_add_limit))
        for name in added:
            print("   ", name)
        print("Changed {} (limit: {})".format(num_changed, file_change_limit))

    # Check: num added
    if num_added > file_add_limit:
        msg = "too many files added: {} vs limit {}".format(num_added,
                                                            file_add_limit)
        error(msg)

    # Check: num changed
    if num_changed > file_change_limit:
        msg = "too many files changed: {} vs limit {}".format(num_changed,
                                                              file_change_limit)
        error(msg)

    # Check: blocked files
    for status, name in lines:
        if is_blocked(name, args):
            msg = "File name is blocked: {}".format(name)
            error(msg)

    # Check: blocked content
    for status, name in lines:
        check_content(name)

    print("Passed")


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args)
