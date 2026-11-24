# Security hook

The pre-commit hook checks staged file names and contents by default.
Use `--local` to check the full working directory before a private-to-public sync.
This mode also checks untracked and ignored files.

The commit-msg hook is a link to the same script.
It checks the commit message for the content blocked in files.
Use `--messages <revision range>` to check the messages of existing commits,
such as `--messages origin/master..HEAD` for the commits a push would publish.
Use `--text <file>` to check other text that will be published,
such as a pull request title or description.

Local scans skip submodule directories recorded in the Git index.
The result does not depend on whether the submodules are populated.
Scan each submodule in its own repository before publishing it.

Run the tests from the repository root.

```sh
python3 -m unittest discover -s git/hooks -p test.py -v
```
