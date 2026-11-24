#!/usr/bin/env python3

import unittest
import os
import shutil
import subprocess
import sys
import unittest.mock

precommit = __import__("pre-commit")


def run_command(command):
    "Run a shell command and ensure it didn't error"
    r = subprocess.run(command, stdout=subprocess.PIPE, encoding='utf-8',
                       shell=True)
    r.check_returncode()


# Dummy arguments object to pass to the precommit script
args = precommit.parse_args([])
hooks_dir = os.path.dirname(os.path.abspath(__file__))
precommit_path = os.path.join(hooks_dir, 'pre-commit.py')


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

    ## Commit message tests ##
    def do_test_bad_message(self, text, **kwargs):
        with self.assertRaises(SystemExit) as e:
            precommit.check_message(text, **kwargs)
        self.assertIn('Commit message contains blocked content',
                      str(e.exception))

    def git_commit(self, *options, env=None):
        'Commit a file with the hooks of this directory installed'
        self.add_file('file')
        return subprocess.run(
            ['git', '-c', 'core.hooksPath=' + hooks_dir, 'commit'] + list(options),
            env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)

    def has_commit(self):
        r = subprocess.run(['git', 'rev-parse', '--verify', '--quiet', 'HEAD'],
                           stdout=subprocess.DEVNULL)
        return r.returncode == 0

    def test_message_blocked_content_fails(self):
        self.do_test_bad_message(
            'rsz: plan fewer trees\n\n'
            'Rapidus2HP, sizing on:\n  time (s): jpeg 193->66\n',
            edited=False)

    def test_message_ok(self):
        precommit.check_message('rsz: plan fewer trees\n\ngf180 is public\n',
                                edited=False)

    def test_message_comments_checked_when_recorded(self):
        text = 'subject\n\n# measured with tsmc\n'
        precommit.check_message(text, edited=True)
        self.do_test_bad_message(text, edited=False)
        self.do_test_bad_message(text, edited=True, cleanup='whitespace')

    def test_message_after_scissors_checked_when_recorded(self):
        text = 'subject\n; {}\n+tsmc\n'.format(precommit.scissors.strip())
        precommit.check_message(text, edited=True, cleanup='scissors',
                                comment=';')
        self.do_test_bad_message(text, edited=False, comment=';')

    def test_commit_blocked_message_fails(self):
        for options in (['-m', 'subject', '-m', 'measured on rapidus2hp'],
                        ['-m', 'subject\n\n# measured on rapidus2hp']):
            with self.subTest(options=options):
                result = self.git_commit(*options)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Commit message contains blocked content',
                              result.stderr)
                self.assertFalse(self.has_commit())

    def test_messages_of_commits(self):
        for i, message in enumerate(('base', 'measured on rapidus2hp', 'fix')):
            self.add_file('file{}'.format(i))
            subprocess.run(['git', 'commit', '-q', '--no-verify', '-m', message],
                           check=True)
        bad = subprocess.run(['git', 'rev-parse', '--short=12', 'HEAD~1'],
                             stdout=subprocess.PIPE, check=True,
                             universal_newlines=True).stdout.strip()

        def scan(revision_range):
            return subprocess.run(
                [sys.executable, precommit_path, '--messages', revision_range],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True)

        result = scan('HEAD~2..HEAD')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Message of commit {} contains blocked content'.format(bad),
                      result.stderr)
        for clean in ('HEAD~1..HEAD', 'HEAD~2..HEAD~2'):
            with self.subTest(revision_range=clean):
                result = scan(clean)
                self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(scan('no-such-ref..HEAD').returncode, 0)

    def test_text_file(self):
        # A path relative to a directory below the top of the repo
        os.mkdir('sub')
        for text, blocked in (('Speed up rsz\n\nMeasured on Rapidus2HP\n', True),
                              ('Speed up rsz\n\ngf180 is public\n', False)):
            with self.subTest(text=text):
                with open('sub/description', 'w') as f:
                    f.write(text)
                result = subprocess.run(
                    [sys.executable, precommit_path, '--text', 'description'],
                    cwd='sub',
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    universal_newlines=True)
                self.assertEqual(result.returncode != 0, blocked, result.stderr)
                if blocked:
                    self.assertIn('Text in description contains blocked content'
                                  ' on line 3', result.stderr)

    def test_commit_good_message_ok(self):
        result = self.git_commit('-m', 'subject')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.has_commit())

    def test_commit_edited_message_ignores_stripped_lines(self):
        # The editor's template names the branch in a comment line and,
        # with --verbose, shows the diff below the scissors line.
        run_command("git checkout -q -b tsmc")
        editor = os.path.abspath('.git/editor.sh')
        with open(editor, 'w') as f:
            f.write('{ echo subject; cat "$1"; } > "$1.new"\n'
                    'grep -q "^# On branch tsmc" "$1.new" || exit 1\n'
                    'grep -q "^+tsmc" "$1.new" || exit 1\n'
                    'mv "$1.new" "$1"\n')
        env = dict(os.environ, GIT_EDITOR='sh ' + editor)
        self.add_file('README.md', 'tsmc')  # content checks skip this file
        result = self.git_commit('--verbose', env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.has_commit())

    def test_message_reports_every_blocked_line(self):
        with self.assertRaises(SystemExit) as e:
            precommit.check_message('tsmc\nfine\nrapidus\n', edited=False)
        self.assertIn('on line 1', str(e.exception))
        self.assertIn('on line 3', str(e.exception))

    def test_message_scissors_cut_only_before_diff(self):
        cut = '#' + precommit.scissors
        # Git records what follows a scissors line that it did not write.
        self.do_test_bad_message('subject\n{}\nmeasured with tsmc\n'.format(cut),
                                 edited=True)
        precommit.check_message(
            'subject\n{}\n# Do not modify\ndiff --git a/f b/f\n+tsmc\n'.format(cut),
            edited=True)

    def test_comment_prefix_last_setting_wins(self):
        for settings, prefix in (
                ([('commentString', ';'), ('commentChar', '%')], '%'),
                ([('commentChar', '%'), ('commentString', ';')], ';'),
                ([('commentChar', '%'), ('commentString', 'AUTO')], None)):
            with self.subTest(settings=settings):
                with open('.git/config', 'a') as f:
                    f.write('[core]\n')
                    for key, value in settings:
                        f.write('\t{} = "{}"\n'.format(key, value))
                self.assertEqual(precommit.comment_prefix(), prefix)

    def test_commit_comment_prefix_as_git_uses_it(self):
        # Git takes % as the prefix here, so it records the line with ;
        run_command("git config core.commentString ';'")
        editor = os.path.abspath('.git/editor.sh')
        with open(editor, 'w') as f:
            f.write('printf "subject\\n\\n; measured on rapidus2hp\\n" > "$1"\n')
        env = dict(os.environ, GIT_EDITOR='sh ' + editor)
        self.add_file('file')
        result = subprocess.run(
            ['git', '-c', 'core.hooksPath=' + hooks_dir,
             '-c', 'core.commentChar=%', 'commit'],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Commit message contains blocked content', result.stderr)
        self.assertFalse(self.has_commit())

    def test_text_on_standard_input(self):
        for text, blocked in (('Measured on Rapidus2HP\n', True),
                              ('gf180 is public\n', False)):
            with self.subTest(text=text):
                result = subprocess.run(
                    [sys.executable, precommit_path, '--text', '-'],
                    input=text,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    universal_newlines=True)
                self.assertEqual(result.returncode != 0, blocked, result.stderr)
                if blocked:
                    self.assertIn('Text on standard input contains blocked content',
                                  result.stderr)
                else:
                    self.assertIn('Passed', result.stdout)

    def test_messages_reports_every_commit_and_bad_range(self):
        for message in ('base', 'measured on rapidus2hp', 'fix', 'tsmc numbers'):
            self.commit(message)

        def scan(revision_range):
            return subprocess.run(
                [sys.executable, precommit_path, '--messages', revision_range],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True)

        result = scan('HEAD~3..HEAD')
        self.assertNotEqual(result.returncode, 0)
        for commit in ('HEAD', 'HEAD~2'):
            self.assertIn('Message of commit {} contains blocked content'
                          .format(self.rev(commit)), result.stderr)
        result = scan('HEAD~1..HEAD~1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Passed', result.stdout)
        result = scan('no-such-ref..HEAD')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ERROR: cannot list the commits of no-such-ref..HEAD',
                      result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def git(self, *command, env=None):
        'Run a git command with the hooks of this directory installed'
        return subprocess.run(
            ['git', '-c', 'core.hooksPath=' + hooks_dir] + list(command),
            env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)

    def editor_env(self, message, keep_template=False):
        '''Returns an environment whose editor writes message, above the
        text git put in the file if keep_template'''
        path = os.path.abspath('.git/message')
        with open(path, 'w') as f:
            f.write(message)
        editor = os.path.abspath('.git/editor.sh')
        with open(editor, 'w') as f:
            if keep_template:
                f.write('cat "{}" "$1" > "$1.new" && mv "$1.new" "$1"\n'
                        .format(path))
            else:
                f.write('cat "{}" > "$1"\n'.format(path))
        return dict(os.environ, GIT_EDITOR='sh ' + editor)

    def test_message_comments_after_scissors_checked_when_recorded(self):
        # No diff follows, so git did not cut here for --verbose
        text = 'subject\n#{}\n# measured with tsmc\n'.format(precommit.scissors)
        precommit.check_message(text, edited=True)
        self.do_test_bad_message(text, edited=True, cleanup='whitespace')

    def test_message_scissors_text_before_diff_checked(self):
        # Git puts only comment lines between its scissors line and the
        # diff, so git did not write this and records the diff too.
        self.do_test_bad_message(
            'subject\n#{}\na pasted patch\ndiff --git a/f b/f\n+tsmc\n'
            .format(precommit.scissors),
            edited=True)

    def test_message_first_scissors_line_is_the_cut(self):
        cut = '#' + precommit.scissors
        self.do_test_bad_message(
            'subject\n{0}\nmeasured with tsmc\n{0}\ndiff --git a/f b/f\n'
            .format(cut),
            edited=True)

    def test_comment_prefix_default_and_auto(self):
        isolated = {'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'}
        with unittest.mock.patch.dict(os.environ, isolated):
            self.assertEqual(precommit.comment_prefix(), '#')
            run_command('git config core.commentChar auto')
            self.assertIsNone(precommit.comment_prefix())

    def test_commit_typed_scissors_line_fails(self):
        # Without --verbose git drops the scissors line as a comment and
        # records the lines below it.
        env = self.editor_env('subject\n\nbody\n#{}\nmeasured on rapidus2hp\n'
                              .format(precommit.scissors))
        result = self.git_commit(env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Commit message contains blocked content on line 5',
                      result.stderr)
        self.assertFalse(self.has_commit())

    def test_commit_auto_comment_prefix_checks_every_line(self):
        run_command("git checkout -q -b tsmc")
        env = self.editor_env('subject\n', keep_template=True)
        self.add_file('file')
        result = self.git('-c', 'core.commentChar=auto', 'commit', env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('# On branch tsmc', result.stderr)
        self.assertFalse(self.has_commit())

    def test_commit_null_editor_checks_every_line(self):
        # GIT_EDITOR is ":" both when git runs no editor, and so records
        # comment lines, and when the user sets it; the hook cannot tell.
        run_command("git checkout -q -b tsmc")
        self.commit('base')
        result = self.git('commit', '--amend',
                          env=dict(os.environ, GIT_EDITOR=':'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('# On branch tsmc', result.stderr)

    def test_commit_merge_message_naming_blocked_branch_fails(self):
        self.commit('base')
        run_command("git checkout -q -b tsmc")
        self.commit('work')
        run_command("git checkout -q -")
        result = self.git('merge', '--no-ff', '--no-edit', 'tsmc')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Merge branch 'tsmc'", result.stderr)

    def test_local_reports_pass(self):
        self.add_file('file')
        result = self.scan_local()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Passed', result.stdout)

    ## Push tests ##
    def commit(self, message):
        'Commit a new file without running the hooks under test'
        self.files = getattr(self, 'files', 0) + 1
        self.add_file('pushed{}'.format(self.files))
        subprocess.run(['git', 'commit', '-q', '--no-verify', '-m', message],
                       check=True)

    def rev(self, revision):
        return subprocess.run(['git', 'rev-parse', '--short=12', revision],
                              stdout=subprocess.PIPE, check=True,
                              universal_newlines=True).stdout.strip()

    def head(self):
        return subprocess.run(['git', 'rev-parse', 'HEAD'],
                              stdout=subprocess.PIPE, check=True,
                              universal_newlines=True).stdout.strip()

    def bare_repo(self, name):
        'Create an empty repo to push to and return its path'
        path = os.path.abspath('.git/{}.git'.format(name))
        subprocess.run(['git', 'init', '-q', '--bare', path], check=True)
        return path

    def add_remote(self, name='origin'):
        path = self.bare_repo(name)
        subprocess.run(['git', 'remote', 'add', name, path], check=True)
        return path

    def git_push(self, refspecs, *options, remote='origin'):
        '''Push the space-separated refspecs to remote with the hooks of
        this directory installed'''
        return self.git('push', '-q', *options, remote, *refspecs.split())

    def run_pre_push(self, url, refs):
        'Run the pre-push hook as git does, with refs on its stdin'
        return subprocess.run(
            [sys.executable, os.path.join(hooks_dir, 'pre-push'), 'origin', url],
            input=refs,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)

    def on_remote(self, branch):
        r = subprocess.run(['git', 'ls-remote', '--exit-code', 'origin',
                            'refs/heads/' + branch],
                           stdout=subprocess.DEVNULL)
        return r.returncode == 0

    def test_push_blocked_messages_fails(self):
        self.add_remote()
        for message in ('base', 'measured on rapidus2hp', 'fix', 'tsmc numbers'):
            self.commit(message)
        result = self.git_push('HEAD:refs/heads/work')
        self.assertNotEqual(result.returncode, 0)
        for commit in ('HEAD', 'HEAD~2'):
            self.assertIn('Message of commit {} contains blocked content'
                          .format(self.rev(commit)), result.stderr)
        self.assertFalse(self.on_remote('work'))

    def test_push_ok(self):
        self.add_remote()
        self.commit('base')
        result = self.git_push('HEAD:refs/heads/work')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.on_remote('work'))

    def test_push_checks_only_unpublished_commits(self):
        self.add_remote()
        self.commit('measured on rapidus2hp')
        result = self.git_push('HEAD:refs/heads/work', '--no-verify')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.commit('fix')
        # The same commits to a new branch and more commits to the old one
        for branch in ('other', 'work'):
            with self.subTest(branch=branch):
                result = self.git_push('HEAD:refs/heads/' + branch)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_push_skips_commits_on_trusted_ref(self):
        self.add_remote()
        self.commit('measured on rapidus2hp')
        run_command('git remote add upstream'
                    ' https://github.com/The-OpenROAD-Project/OpenROAD.git')
        run_command('git update-ref refs/remotes/upstream/master HEAD')
        self.commit('fix')
        result = self.git_push('HEAD:refs/heads/work')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_push_blocked_ref_name_fails(self):
        self.add_remote()
        self.commit('base')
        result = self.git_push('HEAD:refs/heads/tsmc-work')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Name of pushed ref contains blocked content', result.stderr)
        self.assertFalse(self.on_remote('tsmc-work'))

        # Deleting such a ref is allowed
        result = self.git_push('HEAD:refs/heads/tsmc-work', '--no-verify')
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.git_push(':refs/heads/tsmc-work')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.on_remote('tsmc-work'))

    def test_push_to_secure_remote_skipped(self):
        self.commit('measured on rapidus2hp')
        refs = 'refs/heads/tsmc {} refs/heads/tsmc {}\n'.format(self.head(),
                                                               '0' * 40)
        for url, checked in (('/platforms/gf12.git', False),
                             ('or-1:/platforms/tsmc65lp.git', False),
                             ('/platforms/public.git', True)):
            with self.subTest(url=url):
                result = self.run_pre_push(url, refs)
                self.assertEqual(result.returncode != 0, checked, result.stderr)
                if checked:
                    self.assertIn('Name of pushed ref', result.stderr)
                    self.assertIn('Message of commit', result.stderr)
                else:
                    self.assertIn('checking skipped', result.stdout)

    def test_push_cherry_picked_message_fails(self):
        # Git does not run the commit-msg hook for a cherry-pick
        self.add_remote()
        self.commit('base')
        run_command("git checkout -q -b side")
        self.commit('measured on rapidus2hp')
        run_command("git checkout -q -")
        self.commit('other')
        result = self.git('cherry-pick', 'side')
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.git_push('HEAD:refs/heads/work')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Message of commit {} contains blocked content on line 1'
                      .format(self.rev('HEAD')), result.stderr)
        self.assertFalse(self.on_remote('work'))

    def test_push_message_recorded_with_cleanup_option_fails(self):
        # The commit-msg hook cannot see --cleanup, with which git records
        # the comment lines that name the branch.
        self.add_remote()
        run_command("git checkout -q -b tsmc")
        env = self.editor_env('subject\n', keep_template=True)
        result = self.git_commit('--cleanup=whitespace', env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.git_push('HEAD:refs/heads/work')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('# On branch tsmc', result.stderr)
        self.assertFalse(self.on_remote('work'))

    def test_push_to_another_remote_checks_commits_on_the_first(self):
        self.add_remote()
        self.add_remote('public')
        self.commit('measured on rapidus2hp')
        result = self.git_push('HEAD:refs/heads/work', '--no-verify')
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.git_push('HEAD:refs/heads/work', remote='public')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Message of commit {} contains blocked content'
                      .format(self.rev('HEAD')), result.stderr)

    def test_push_to_url_checks_only_new_commits(self):
        # A remote given by URL has no remote-tracking refs
        url = self.bare_repo('unnamed')
        self.commit('measured on rapidus2hp')
        result = self.git_push('HEAD:refs/heads/work', '--no-verify', remote=url)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.commit('fix')
        result = self.git_push('HEAD:refs/heads/work', remote=url)
        self.assertEqual(result.returncode, 0, result.stderr)
        # Nothing shows that a new ref's commits are already at the URL
        result = self.git_push('HEAD:refs/heads/other', remote=url)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Message of commit {} contains blocked content'
                      .format(self.rev('HEAD~1')), result.stderr)

    def test_push_over_commits_that_were_not_fetched(self):
        url = self.add_remote()
        self.commit('base')
        result = self.git_push('HEAD:refs/heads/work')
        self.assertEqual(result.returncode, 0, result.stderr)

        # Someone else pushes a commit that this repo does not have
        other = os.path.abspath('.git/other')
        subprocess.run(['git', 'clone', '-q', '-b', 'work', url, other],
                       check=True, stderr=subprocess.DEVNULL)
        with open(os.path.join(other, 'theirs'), 'w') as f:
            print('theirs', file=f)
        for command in (['add', 'theirs'],
                        ['commit', '-q', '--no-verify', '-m', 'theirs'],
                        ['push', '-q', '--no-verify', 'origin', 'work']):
            subprocess.run(['git', '-C', other] + command, check=True)

        self.commit('tsmc numbers')
        result = self.git_push('HEAD:refs/heads/work', '--force')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Message of commit {} contains blocked content'
                      .format(self.rev('HEAD')), result.stderr)
        self.assertEqual(result.stderr.count('contains blocked content'), 1)

        subprocess.run(['git', 'commit', '-q', '--no-verify', '--amend',
                        '-m', 'fix'], check=True)
        result = self.git_push('HEAD:refs/heads/work', '--force')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_push_several_refs_reports_each(self):
        self.add_remote()
        self.commit('base')
        run_command("git branch clean")
        self.commit('measured on rapidus2hp')
        result = self.git_push('clean:refs/heads/clean HEAD:refs/heads/work'
                               ' clean:refs/heads/tsmc-work')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Message of commit {} contains blocked content'
                      .format(self.rev('HEAD')), result.stderr)
        self.assertIn('Name of pushed ref contains blocked content :\n'
                      '  refs/heads/tsmc-work', result.stderr)
        self.assertEqual(result.stderr.count('contains blocked content'), 2)
        self.assertFalse(self.on_remote('clean'))

    def test_push_tags(self):
        self.add_remote()
        self.commit('base')
        for tag in ('v1', 'tsmc-v1'):
            subprocess.run(['git', 'tag', '-a', '-m', 'release', tag], check=True)
        result = self.git_push('refs/tags/v1')
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.git_push('refs/tags/tsmc-v1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Name of pushed ref contains blocked content :\n'
                      '  refs/tags/tsmc-v1', result.stderr)

        # The commits that a tag publishes
        self.commit('measured on rapidus2hp')
        subprocess.run(['git', 'tag', '-a', '-m', 'release', 'v2'], check=True)
        result = self.git_push('refs/tags/v2')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Message of commit {} contains blocked content'
                      .format(self.rev('HEAD')), result.stderr)

    def test_push_checks_commits_on_untrusted_refs(self):
        self.add_remote()
        self.commit('measured on rapidus2hp')
        # A fork's master, and another branch of a trusted remote
        run_command('git remote add fork https://github.com/someone/OpenROAD.git')
        run_command('git update-ref refs/remotes/fork/master HEAD')
        run_command('git remote add upstream'
                    ' https://github.com/The-OpenROAD-Project/OpenROAD.git')
        run_command('git update-ref refs/remotes/upstream/feature HEAD')
        self.commit('fix')
        result = self.git_push('HEAD:refs/heads/work')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Message of commit {} contains blocked content'
                      .format(self.rev('HEAD~1')), result.stderr)

    def test_push_with_unfetched_trusted_remote_ok(self):
        self.add_remote()
        run_command('git remote add upstream'
                    ' https://github.com/The-OpenROAD-Project/OpenROAD.git')
        self.commit('base')
        result = self.git_push('HEAD:refs/heads/work')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_trusted_refs(self):
        self.commit('base')
        for name, url in (
                ('public', 'https://github.com/The-OpenROAD-Project/OpenROAD.git'),
                ('private', 'git@github.com:The-OpenROAD-Project-private/'
                 'OpenROAD-flow-scripts.git'),
                ('fork', 'https://github.com/someone/OpenROAD.git'),
                ('unfetched', 'ssh://git@github.com/The-OpenROAD-Project/'
                 'OpenROAD-flow-scripts')):
            subprocess.run(['git', 'remote', 'add', name, url], check=True)
        for ref in ('public/master', 'private/master', 'private/feature',
                    'fork/master'):
            run_command('git update-ref refs/remotes/{} HEAD'.format(ref))
        self.assertEqual(sorted(precommit.trusted_refs()),
                         ['refs/remotes/private/master',
                          'refs/remotes/public/master'])

    def test_is_commit(self):
        self.commit('base')
        for revision in ('HEAD', self.head()):
            self.assertTrue(precommit.is_commit(revision), revision)
        for revision in ('0' * 40, 'no-such-ref', 'HEAD:pushed1', '--all'):
            self.assertFalse(precommit.is_commit(revision), revision)

if __name__ == '__main__':
    unittest.main()
