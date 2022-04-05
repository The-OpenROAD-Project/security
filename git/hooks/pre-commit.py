#!/usr/bin/env python3

import argparse
import gzip
import hashlib
import os
import re
import subprocess
import sys

print("Running pre-commit security hook....")

# Limits for rules
file_add_limit    = 20
file_change_limit = 50

# The following patterns are regular expressions and are matched
# case-insensitive.  They are matched anywhere with the string
# and can have leading or trailing characters and still match.

# Blocked paths (unless allowed below).
blocked_path_patterns = [
    r"flow/",
    r"\.gds",
    r"\.lef",
    r"\.def$",
    r"\.cdl",
    r"\.cal",
    r"\.v$",
    r"\.db",
    r"\.lib",
    r"\.t?gz",
    r"\.tar",
    r"tsmc",
    r"intel",
    r"gf\d+",
    r"\d+lp",    # Invecas
    r"sc\d+",    # ARM-style names
    r"cln\d+",   # eg CLN65 (for ARM)
    r"scc9gena", # Sky90 library
    r"sky90"     # Sky90
]

# Allowed paths are exceptions to blocked paths above.
allowed_path_patterns = [
    r"^\.git/",
    r"^flow/designs",
    r"^flow/docs",
    r"^flow/platforms/nangate45",
    r"^flow/platforms/sky130",
    r"^flow/platforms/asap7",
    r"^flow/scripts",
    r"^flow/test",
    r"^flow/tutorials",
    r"^flow/util",
    r"^flow/README.md",
    r"^flow/Makefile",
    r"^flow/Makefile.no_drt",
    r"^(tools/OpenROAD/)?src/grt/test",
    r"^(tools/OpenROAD/)?src/ICeWall/test",
    r"^(tools/OpenROAD/)?src/pad/test",
    r"^((tools/OpenROAD/)?src/odb/)?src/[ld]ef(56)?/TEST",
    r"^((tools/OpenROAD/)?src/odb/)?test",
    r"^(tools/OpenROAD/)?src/sta/examples",
    r"^(tools/OpenROAD/)?src/sta/test",
    r"^(tools/OpenROAD/)?src/psm/test",
    r"^(tools/OpenROAD/)?src/cts/test",
    r"^(tools/OpenROAD/)?src/mpl2?/test",
    r"^(tools/OpenROAD/)?src/rcx/test",
    r"^(tools/OpenROAD/)?src/ant/test",
    r"^(tools/OpenROAD/)?src/dbSta/test",
    r"^(tools/OpenROAD/)?src/ifp/test",
    r"^(tools/OpenROAD/)?src/ppl/test",
    r"^(tools/OpenROAD/)?src/dpl/test",
    r"^(tools/OpenROAD/)?src/dpo/test",
    r"^(tools/OpenROAD/)?src/pdn/test",
    r"^(tools/OpenROAD/)?src/replace/test",
    r"^(tools/OpenROAD/)?src/gpl/test",
    r"^(tools/OpenROAD/)?src/rsz/test",
    r"^(tools/OpenROAD/)?src/tap/test",
    r"^(tools/OpenROAD/)?src/par/test",
    r"^(tools/OpenROAD/)?src/drt/test",
    r"^(tools/OpenROAD/)?src/psm/test",
    r"^(tools/OpenROAD/)?src/pdrev/test",
    r"^(tools/OpenROAD/)?src/pdr/test",
    r"^(tools/OpenROAD/)?src/rmp/test",
    r"^(tools/OpenROAD/)?src/pdngen/test",
    r"^(tools/OpenROAD/)?src/PartitionMgr/test",
    r"^(tools/OpenROAD/)?src/TritonCTS/test",
    r"^(tools/OpenROAD/)?src/PDNSim/test",
    r"^(tools/OpenROAD/)?test",
    r"^tools/yosys",
]

# Files may not contain these patterns in their content anywhere (not
# just the changed portion).  All staged files are checked, even
# "allowed" files - there should still be no bad content in allowed
# files.
#
# Uses compiled expression for performance.
block_content_patterns = \
    re.compile(r"""
       gf\d\d+    # eg gf12, gf14
     | tsmc       # eg tsmc65lp
     | \d+lp      # eg 12LP (for Invecus)
     | \barm\b    # eg ARM
     | cln\d+     # eg CLN65 (for ARM)
     | cypress    # eg Cypress Semiconductor
     | intel(?!l) # eg Intel (but not intelligent)
    """, re.VERBOSE | re.IGNORECASE)

# Files to skip content checks on
skip_content_patterns = [
    r"\.gif$",
    r"\.jpg$",
    r"\.png$",
    r"\.pdf$",
    r"\.gif$",
    r"\.odt$",
    r"\.xlsx$",
    r"\.a$",
    r"^src/sta/app/sta$",
    r"\.dat$",  # eg POWV9.dat
    r"\.gds(\.orig)?$",
    r"^README.md$",
    r"^(tools/OpenROAD/)?docs/index.(md|rst)$",
    r"^(tools/OpenROAD/)?docs/user/GettingStarted.(md|rst)$",
    r"^flow/README.md$",
    r"^(tools/OpenROAD/)?src/drt/src", # until cleaned up
    r"^(tools/OpenROAD/)?src/drt/cmake", # .../intel/vtune
    r"^(tools/OpenROAD/)?src/gpl/README.md$",
    r"^(flow/platforms/)?sky130hd/chameleon",
    r"^(flow/designs/)?sky130hd/chameleon",
    r"^tools/yosys/",
    r"^\.git/",
    r"^flow/designs/.*/metadata.*-ok.json$",
    r"^flow/designs/.*/config.mk$",
    r"^flow/designs/.*/config_hier.mk$",
    r"^flow/designs/.*/wrappers.tcl$",
    r"^flow/designs/.*/macros.v$",
    r"^flow/designs/src/.*\.sv2v\.v$",
    r"^flow/scripts/add_routing_blk.tcl$",
    r"^flow/scripts/floorplan.tcl$",
    r"^flow/test/core_tests.sh$",
    r"^flow/test/smoke.sh$",
    r"^flow/util/cell-veneer/wrap_stdcells.tcl",
    r"^flow/util/cell-veneer/lefdef.tcl",
    r"^flow/util/calBuffer.py",
    r"^flow/util/calPath.py",
    r"^flow/util/run.sh",
    r"^flow/Makefile$",
]

# For large files we keep an md5 hash of the contents to avoid the expense
# of scanning them with the block_content_patterns regex which is slow.
md5_whitelist = set((
    # OpenROAD
    'a1a371511c98b51fbaa46041314718fd', # test/sky130hs/sky130_fd_sc_hs__tt_025C_1v80.lib before 04/04/2022
    '63f66e54f4d04b374e60756388e9c116', # test/sky130hs/sky130_fd_sc_hs__tt_025C_1v80.lib
    '25707ca69a393abfefe381ab52b82543', # test/sky130hd/sky130_fd_sc_hd__ff_n40C_1v95.lib
    'b29ffb80bf70e61b7064796c8702eb45', # src/rcx/test/generate_pattern.spefok
    '0f1a956ff22a003be485a678b3877fd5', # src/rcx/test/generate_pattern.defok
    '303c92cc0ec313c0630d84f94313f6ac', # src/rcx/test/generate_pattern.vok
    'd80867b517b2448febf60860bf663374', # src/gpl/test/large01.defok
    '1129d48daf4119864762d3afae44700c', # src/gpl/test/large01.def
    'f66e8a49010debd35833f159dad1d5c8', # src/gpl/test/large02.defok
    '8ce7ee36cde5a01fca6b800a4090c5dc', # src/gpl/test/large02.def
    'e9e4daefed9083224832fbe262d0ea5d', # src/gpl/test/macro03.def
    'b49d16b2ca57c7dfe2e690bf1b4c0d57', # src/gpl/test/medium03.defok
    '965c8a3c3b424708583d48ee1f9ad931', # src/gpl/test/medium03.def
    '6725a64db47a2c4f3a9eba59c149ef66', # src/gpl/test/medium04.def
    '13bd6497ece4785e873ff699eef79f41', # src/gpl/test/medium04.defok
    '338775fa5ff59a87225454f9e3fb7d33', # src/pdn/test/soc_bsg_black_parrot_nangate45.defok
    '11c59e5f428eb51deee617620ed585bf', # src/pdn/test/soc_bsg_black_parrot_nangate45.pad_offset.defok
    '880b1b8b9282e5f9033cf5d6d4c4e6b6', # src/pdn/test/pads_black_parrot.defok (old)
    '0ade01392aacde0bc812c1d00d8af487', # src/pdn/test/pads_black_parrot.defok (new)
    'bff2e7589ef7e3e5cfa731b231845dcf', # src/pdn/test/pads_black_parrot_flipchip.defok (old)
    'c129ce8592c28e0fa7676d5465298dd7', # src/pdn/test/pads_black_parrot_flipchip.defok (new)

    # OpenROAD-flow-scripts
    '2d74c6a29a8cd18536ec332accfa76d1', # flow/platforms/sky130ram/sky130_sram_1rw1r_80x64_8/sky130_sram_1rw1r_80x64_8.lef
    '17d9ce812cf1b635c392750ac0ec69c3', # flow/platforms/sky130ram/sky130_sram_1rw1r_128x256_8/sky130_sram_1rw1r_128x256_8.lef
    '3d196f7e32be942538db4021fdd72927', # flow/platforms/sky130ram/sky130_sram_1rw1r_64x256_8/sky130_sram_1rw1r_64x256_8.lef
    '599c96df532d6b334463cecb6b7d2f78', # flow/platforms/sky130hs/lib/sky130_fd_sc_hs__tt_100C_1v80.lib
    '3541e22e1ed76cddd2b104c8938b70e7', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SLVT_SS_nldm_201020.lib
    '6756222941e7d68d3c9cb90984c1bf83', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SLVT_TT_nldm_201020.lib
    'a3caea338431c290089ac110a9839f62', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SRAM_FF_nldm_201020.lib
    '557414126cb483fa25a66e3d17f76fe1', # flow/platforms/asap7/lib/asap7sc7p5t_OA_RVT_SS_nldm_201020.lib
    '421d20d1f12945d4979ae1c78da9aa2e', # flow/platforms/asap7/lib/asap7sc7p5t_AO_RVT_SS_nldm_201020.lib
    '35dc584334ba616972838ab7b4eadaea', # flow/platforms/asap7/lib/asap7sc7p5t_AO_LVT_TT_nldm_201020.lib
    '9e56e6d9790f1cd904914b41c6c0faad', # flow/platforms/asap7/lib/asap7sc7p5t_AO_RVT_FF_nldm_201020.lib
    'f514f36645928a32a7fbd1a232420831', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SRAM_SS_nldm_201020.lib
    '1d0a4b12b973072e2b8ac0c2d80d2a08', # flow/platforms/asap7/lib/asap7sc7p5t_OA_RVT_FF_nldm_201020.lib
    'cb552f32d836cee62e8fd8758ace59bc', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SRAM_TT_nldm_201020.lib
    'a8bb2a328dfaede8e653588dc9b1c062', # flow/platforms/asap7/lib/asap7sc7p5t_OA_LVT_TT_nldm_201020.lib
    'c801c520546a03e5fca703e6efaf4d44', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SLVT_FF_nldm_201020.lib
    'c0160f0735003cdda388782b7d3c2956', # flow/platforms/asap7/lib/asap7sc7p5t_AO_RVT_TT_nldm_201020.lib
    'a36d097e6c3d273f91c4ff4645ebd4a1', # flow/platforms/asap7/lib/asap7sc7p5t_AO_LVT_FF_nldm_201020.lib
    '353c6442fd0a631fe92dd1b4b53c7a57', # flow/platforms/asap7/lib/asap7sc7p5t_OA_LVT_FF_nldm_201020.lib
    '4aa64e2f86ac82f74fd7f85755e96de4', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SLVT_TT_nldm_201020.lib
    'b13ff982123b3ec7a3123e987a976266', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SLVT_SS_nldm_201020.lib
    'c5c12056efdf6971aca43fef7f7b93cd', # flow/platforms/asap7/lib/asap7sc7p5t_OA_RVT_TT_nldm_201020.lib
    '73ce20b16bdd41403b3785e592dbee13', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SRAM_FF_nldm_201020.lib
    'f5b5ea21025ddec37e157b563f7f4db8', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SRAM_TT_nldm_201020.lib
    'd3cbcdde427e44edc87e7c750303b6ad', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SRAM_SS_nldm_201020.lib
    'dda503333c1948a41fd17296b8839a09', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SLVT_FF_nldm_201020.lib
    'cdd685451262808f8f77bd8040c8b230', # flow/platforms/asap7/lib/asap7sc7p5t_OA_LVT_SS_nldm_201020.lib
    '6d1b8586754b2cdcde73695662c2ab65', # flow/platforms/asap7/lib/asap7sc7p5t_AO_LVT_SS_nldm_201020.lib

))

md5_whitelist_cutoff = 15 * 1024 * 1024 # 15 Mb

# Commits to these repos aren't checked as they are
# never to be made public and are intended for confidential
# data.
repos_secure = set((
    '(.*dfm:)?/home/zf4_projects/OpenROAD-guest/platforms/gf12.git',
    '(.*dfm:)?/home/zf4_projects/OpenROAD-guest/platforms/gf55.git',
    '(.*dfm:)?/home/zf4_projects/OpenROAD-guest/platforms/tsmc65lp.git',
    '(.*dfm:)?/home/zf4_projects/OpenROAD-guest/platforms/intel22.git',
))

def error(msg):
    msg = '\n\nERROR: {}\n\nTo request an exception please file an issue on GitHub' \
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


def check_content(name, args, whole_file=False):
    for pattern in skip_content_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            if args.verbose:
                print("Skipping content check on {}".format(name))
            return

    # Submodules updates will show up as names to be checked but they
    # should have their contents checked when the submodule itself
    # was committed to. Skip them here.
    if os.path.isdir(name):
        print("Skipping content check on subdir {}".format(name))
        return

    if whole_file:
        if os.path.islink(name):
            if args.verbose:
                print("Skipping link", name)
            return

        # Check big files in the md5 whitelist
        size = os.stat(name).st_size
        if size >= md5_whitelist_cutoff:
            with open(name, 'rb') as f:
                contents = f.read()
            md5_hash = hashlib.md5(contents).hexdigest()
            if md5_hash in md5_whitelist:
                if args.verbose:
                    print('Skipping big {} with hash {}',  name, md5_hash)
                return
            else:
                error('File {} is big but not whitelisted (hash {})'.format(name, md5_hash))

        if name.endswith('.gz'):
            with gzip.open(name, mode='rt', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        else:
            with open(name, encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
    else:
        # the : in front of the file name gets the staged version of the
        # file, not what is currently on disk unstaged which could be
        # different (and possibly not contain the keyword).  We check the
        # whole file not just the changed portion.
        lines = run_command('git show :{}'.format(name))
    for cnt, line in enumerate(lines):
        # re.search matches anywhere in the line
        if re.search(block_content_patterns, line):
            msg = "File {} contains blocked content" \
                " on line {} :\n  {}" \
                .format(name,
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
    parser.add_argument('--local', action='store_true')
    parser.add_argument('--report', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    return parser.parse_args(args)


def walk_error(e):
    raise e


def local(top, args):
    """Check the local tree not the git diff.  This is for private to
    public prechecking. """
    for root, dirs, files in os.walk(top,
                                     onerror=walk_error):
        assert(root.startswith(top))
        if root == top:
            root = ''
        else:
            root = root[len(top)+1:]
        for name in files:
            full_name = os.path.join(root, name)
            if is_blocked(full_name, args):
                msg = "File name is blocked: {}".format(full_name)
                error(msg)
            check_content(full_name, args, whole_file=True)


def check_remotes_secure():
    repos = run_command('git remote --verbose')
    # Example line:
    # origin	/home/zf4_projects/OpenROAD-guest/platforms/gf12.git (fetch)
    for line in repos:
        if not line: # local repo (used for testing)
            return False
        (name, url, _) = re.split('\t| \(', line)
        found = False
        for repo_pattern in repos_secure:
            if re.match(repo_pattern, url):
                found = True
                break
        if not found:
            return False
    return True

def main(args):
    # subprocess.run doesn't exist before 3.5
    if sys.version_info < (3, 5):
        sys.exit("Python 3.5 or later is required")

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

    if args.local:
        local(top, args)
        return

    if check_remotes_secure():
        print('All git remotes are secure, checking skipped')
        return

    # Get status of the staged files
    lines = run_command('git diff --cached --name-status')
    if len(lines[0]) == 0:
        sys.exit('ERROR: Nothing is staged')

    # Split the lines in status & file.  Filenames containing whitespace
    # are problematic so don't do that.
    lines = [l.split() for l in lines]
    for l in lines:
        if l[0].startswith('R'): # Handle renames
            assert(len(l) == 3)
            l[0] = 'R'  # Strip off score
            del l[1]    # remove old name
        assert(len(l) == 2)     # sanity check : <status> <file>
        assert(len(l[0]) == 1)  # sanity check : <status> is one char

    # Newly added files
    added = [f[1] for f in lines if f[0] == 'A']
    num_added = len(added)

    # Deleted files
    deleted = [f[1] for f in lines if f[0] == 'D']
    num_deleted = len(deleted)

    # This is all other changes, including modify, rename, copy
    num_changed = len(lines) - num_added - num_deleted

    if (args.report):
        print("Added {} (limit: {})".format(num_added, file_add_limit))
        for name in added:
            print("   ", name)
        print("Deleted {} (limit: none)".format(num_deleted))
        for name in deleted:
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
        if status != 'D': # deleted are always ok
            check_content(name, args)

    print("Passed")


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args)
