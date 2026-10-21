# Security hook

The pre-commit hook checks staged file names and contents by default.
Use `--local` to check the full working directory before a private-to-public sync.
This mode also checks untracked and ignored files.

Local scans skip submodule directories recorded in the Git index.
The result does not depend on whether the submodules are populated.
Scan each submodule in its own repository before publishing it.

Run the tests from the repository root.

```sh
python3 -m unittest discover -s git/hooks -p test.py -v
```
