#!/usr/bin/env python3

import unittest
import os
import shutil
import subprocess
import sys

precommit = __import__("pre-commit")


def run_command(command):
    "Run a shell command and ensure it didn't error"
    r = subprocess.run(command, stdout=subprocess.PIPE, encoding='utf-8',
                       shell=True)
    r.check_returncode()


# Dummy arguments object to pass to the precommit script
args = precommit.parse_args([])
precommit_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'pre-commit.py')


class TestBlock(unittest.TestCase):
    def setUp(self):
        'Setup a dummy repo to test in'
        os.mkdir("test_area")
        run_command("git init test_area")
        os.chdir("test_area")

    def tearDown(self):
        os.chdir("..")
        shutil.rmtree("test_area")
        pass

    ## Helpers ##
    def add_file(self, path, content=''):
        'Commit a file to the repo with given contents'
        dirs = os.path.dirname(path)
        if dirs:
            os.makedirs(dirs)
        with open(path, 'w') as f:
            print(content, file=f)
        run_command("git add {}".format(path))

    def add_files(self, cnt):
        'Add cnt files to the repo'
        for i in range(cnt):
            self.add_file('file{}'.format(i))

    def add_submodule(self, path):
        subprocess.run([
            'git', 'update-index', '--add', '--cacheinfo', '160000',
            '1234567890123456789012345678901234567890', path], check=True)
        os.makedirs(path)

    def scan_local(self):
        return subprocess.run(
            [sys.executable, precommit_path, '--local'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)

    def do_test_bad_file(self, path):
        'Create a file and make sure it is blocked by precommit path check'
        self.add_file(path)
        with self.assertRaises(SystemExit) as e:
            precommit.main(args)
        self.assertIn('name is blocked', str(e.exception))

    def do_test_good_file(self, path):
        'Create a file and make sure it is allowed by precommit'
        self.add_file(path)
        # passes if no exception raised
        precommit.main(args)

    def do_test_good_content(self, content=''):
        'Create a file and make sure it is allowed by precommit content check'
        self.add_file("test_file", content)
        # passes if no exception raised
        precommit.main(args)

    def do_test_bad_content(self, content=''):
        'Create a file and make sure it is block by precommit content check'
        self.add_file("test_file", content)
        with self.assertRaises(SystemExit) as e:
            precommit.main(args)
        self.assertIn('contains blocked content', str(e.exception))

    ## Blocked / allowed paths tests ##
    def test_gf12_fails(self):
        self.do_test_bad_file('dir/some_gf12_data')

    def test_new_platform_fails(self):
        self.do_test_bad_file('flow/platforms/7nm')

    def test_verilog_fails(self):
        self.do_test_bad_file('foo.v')

    def test_gds_fails(self):
        self.do_test_bad_file('foo.gds2')

    def test_lef_fails(self):
        self.do_test_bad_file('foo.lef.gz')

    def test_cal_fails(self):
        self.do_test_bad_file('foo.cal')

    def test_cdl_fails(self):
        self.do_test_bad_file('a/b/foo.cdl')

    def test_lib_fails(self):
        self.do_test_bad_file('foo.lib')

    def test_gz_fails(self):
        self.do_test_bad_file('foo.gz')
        self.do_test_bad_file('foo.tgz')

    def test_tar_fails(self):
        self.do_test_bad_file('foo.tar')

    def test_tsmc_fails(self):
        self.do_test_bad_file('tsmc65lp')

    def test_tsmc_lib_fails(self):
        self.do_test_bad_file('cln12.lef')

    def test_sky90_fails(self):
        self.do_test_bad_file('sky90')

    def test_sky90_lib_fails(self):
        self.do_test_bad_file('scc9gena.lef')

    def test_arm_fails(self):
        self.do_test_bad_file('sc9mcpp84_12lp_base_rvt')
        self.do_test_bad_file('sc300mcpp')

    def test_rapidus_fails(self):
        self.do_test_bad_file('SC2HP')

    def test_rapidus2_fails(self):
        self.do_test_bad_file('cmos2hp_tech')

    def test_flow_allowed_only_if_at_start_of_path(self):
        self.do_test_bad_file('gf14/flow/designs')

    def test_nangate_update_ok(self):
        self.do_test_good_file('flow/platforms/nangate45/netlist.v')

    def test_design_verilog_ok(self):
        self.do_test_good_file('flow/designs/foo.v')

    ## Size of adds / changes tests ##
    def test_too_many_adds_fails(self):
        cnt = precommit.file_add_limit + 1
        self.add_files(cnt)
        with self.assertRaises(SystemExit) as e:
            precommit.main(args)
        self.assertIn('too many files added', str(e.exception))

    def test_too_many_changes_fails(self):
        # setup by committing files
        cnt = precommit.file_change_limit + 1
        self.add_files(cnt)
        run_command("git commit -m 'msg' --no-verify")

        # Continue setup by modifying the files
        for i in range(cnt):
            with open('file{}'.format(i), 'w') as f:
                print('modified', file=f)

        # Finish setup by staging all the modified files
        run_command("git add .")

        # now test
        with self.assertRaises(SystemExit) as e:
            precommit.main(args)
        self.assertIn('too many files changed', str(e.exception))

    ## Merges ##
    trusted_url = 'git@github.com:The-OpenROAD-Project/OpenROAD.git'

    def setup_merge(self, side, url=trusted_url, branch='master'):
        '''Commit side() on a side branch, publish it as
        refs/remotes/upstream/<branch> of a remote at url (when url is
        given), then start a merge of it into a diverged HEAD with
        --no-commit so the hook sees the staged merge.'''
        self.add_file('base', 'base')
        run_command("git commit -q -m base --no-verify")
        run_command("git checkout -q -b side")
        side()
        run_command("git add -A")
        run_command("git commit -q -m side --no-verify")
        run_command("git checkout -q -")
        with open('base', 'w') as f:
            print('diverged', file=f)
        run_command("git commit -q -am diverge --no-verify")
        if url:
            subprocess.run(['git', 'remote', 'add', 'upstream', url], check=True)
            run_command("git update-ref refs/remotes/upstream/{} side"
                        .format(branch))
        run_command("git merge -q --no-commit --no-ff side")

    def side_adds(self, cnt, prefix='side'):
        def side():
            for i in range(cnt):
                self.add_file('{}{}'.format(prefix, i))
        return side

    def test_merge_adds_from_trusted_master_ok(self):
        self.setup_merge(self.side_adds(precommit.file_add_limit + 1))
        precommit.main(args)

    def test_merge_changes_from_trusted_master_ok(self):
        cnt = precommit.file_change_limit + 1
        self.add_files(cnt)

        def side():
            for i in range(cnt):
                with open('file{}'.format(i), 'w') as f:
                    print('modified', file=f)
        self.setup_merge(side)
        precommit.main(args)

    def test_merge_trusted_url_ignores_case(self):
        url = 'git@github.com:The-OpenROAD-Project-Private/OpenROAD.git'
        self.setup_merge(self.side_adds(precommit.file_add_limit + 1), url=url)
        precommit.main(args)

    def test_merge_untrusted_remote_fails(self):
        for url in ('git@github.com:The-OpenROAD-Project-staging/OpenROAD.git',
                    'git@github.com:The-OpenROAD-Project-private/bitdeer.git',
                    'git@evilgithub.com:The-OpenROAD-Project/OpenROAD.git',
                    'https://evil.com/github.com/The-OpenROAD-Project/OpenROAD',
                    'git@github.com:The-OpenROAD-Project/OpenROAD.git.evil',
                    None):
            with self.subTest(url=url):
                self.tearDown()
                self.setUp()
                self.setup_merge(
                    self.side_adds(precommit.file_add_limit + 1), url=url)
                with self.assertRaises(SystemExit) as e:
                    precommit.main(args)
                self.assertIn('too many files added', str(e.exception))

    def test_merge_trusted_remote_non_master_fails(self):
        self.setup_merge(self.side_adds(precommit.file_add_limit + 1),
                         branch='feature')
        with self.assertRaises(SystemExit) as e:
            precommit.main(args)
        self.assertIn('too many files added', str(e.exception))

    def test_merge_trusted_plus_local_adds_fails(self):
        self.setup_merge(self.side_adds(precommit.file_add_limit + 1))
        for i in range(precommit.file_add_limit + 1):
            self.add_file('local{}'.format(i))
        with self.assertRaises(SystemExit) as e:
            precommit.main(args)
        self.assertIn('too many files added', str(e.exception))

    def test_merge_trusted_blocked_file_fails(self):
        self.setup_merge(lambda: self.add_file('foo.lib'))
        with self.assertRaises(SystemExit) as e:
            precommit.main(args)
        self.assertIn('name is blocked', str(e.exception))

    def test_merge_trusted_blocked_content_fails(self):
        self.setup_merge(lambda: self.add_file('notes.txt', 'ARM Limited'))
        with self.assertRaises(SystemExit) as e:
            precommit.main(args)
        self.assertIn('contains blocked content', str(e.exception))

    def test_merge_remote_name_not_run_by_shell(self):
        marker = os.path.abspath('injected')
        self.setup_merge(self.side_adds(1))
        subprocess.run(['git', 'remote', 'add',
                        'x;touch${IFS}' + marker + ';#', self.trusted_url],
                       check=True)
        precommit.main(args)
        self.assertFalse(os.path.exists(marker))

    ## Local tree scans ##
    def test_local_scan_skips_submodule_contents(self):
        for path in ('third-party/sv-elab', 'vendor/with space'):
            self.add_submodule(path)
            for populated in (False, True):
                with self.subTest(path=path, populated=populated):
                    if populated:
                        presets = os.path.join(path, 'third_party/slang')
                        os.makedirs(presets)
                        with open(os.path.join(presets, 'CMakePresets.json'), 'w') as f:
                            f.write('{"name": "win64-arm-release"}\n')
                        with open(os.path.join(path, 'blocked.v'), 'w') as f:
                            f.write('module example; endmodule\n')
                    result = self.scan_local()
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_local_scan_checks_parent_contents(self):
        self.add_submodule('third-party/sv-elab')
        for path in ('notes.txt', 'third-party/sv-elab-copy/CMakePresets.json'):
            with self.subTest(path=path):
                self.add_file(path, 'ARM Limited')
                result = self.scan_local()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('File {} contains blocked content'.format(path),
                              result.stderr)
                os.remove(path)

    def test_local_scan_checks_untracked_contents(self):
        self.add_file('.gitignore', 'ignored.txt')
        with open('ignored.txt', 'w') as f:
            f.write('ARM Limited\n')
        result = self.scan_local()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('File ignored.txt contains blocked content', result.stderr)

    ## Blocked content tests ##
    def test_gf_content_fails(self):
        self.do_test_bad_content('gf12 secrets')

    def test_arm_content_fails(self):
        self.do_test_bad_content('ARM Limited')

    def test_invecus_content_fails(self):
        self.do_test_bad_content('data for 12LP')

    def test_tsmc_content_fails(self):
        self.do_test_bad_content('\n\n\n  tsmc')

    def test_tsmc_lib_content_fails(self):
        self.do_test_bad_content('\n\n\n  CLN65')        

    def test_cypress_content_fails(self):
        self.do_test_bad_content('\n\n\n  Cypress')

    def test_rapidus_content_fails(self):
        self.do_test_bad_content('\n\n\n  Rapidus')

    def test_gf180_content_allowed(self):
        self.do_test_good_content('gf180 is public')

if __name__ == '__main__':
    unittest.main()
