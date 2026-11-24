# Security hook

The pre-commit hook checks staged file names and contents by default.
Use `--local` to check the full working directory before a private-to-public sync.
This mode also checks untracked and ignored files.

The commit-msg and pre-push hooks are links to the same script.
The commit-msg hook checks the commit message for the content blocked in files.
It cannot see the `--cleanup` and `--verbose` options of `git commit`,
and git does not run it for `cherry-pick`, `rebase` or `--no-verify`.
The pre-push hook covers those cases.
It checks the name of each pushed ref and the recorded messages of the commits the push publishes.
Commits already on the remote or on a trusted branch are not checked again.

Use `--messages <revision range>` to check the messages of existing commits,
such as `--messages origin/master..HEAD`.
Use `--text <file>` to check other text that will be published,
such as a pull request title or description.
Use `--text -` to read the text from standard input.

Local scans skip submodule directories recorded in the Git index.
The result does not depend on whether the submodules are populated.
Scan each submodule in its own repository before publishing it.

Run the tests from the repository root.

```sh
python3 -m unittest discover -s git/hooks -p test.py -v
```
