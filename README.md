git-stats: compare performance statistics across branches
=========================================================

`git-stats` allows you to compare the performance of different branches
of your project.
The tests should produce quantitative results which you want to do some
further analysis on.

Examples
--------
If you're making major changes to the internals of your project to try to
achieve a speedup or improve some other metric, it's very helpful to keep
different versions on multiple branches and quantify the performance
on each.
For example, you can just measure the speed of your unit tests:

    $ git show master:tests/git-stats/time-unit-tests
    #!/bin/bash
    nosetests tests/git-stats/unit-tests | (
        # Strip time from line: "Ran X tests in X.XXXs"
        awk '/Ran [0-9]+ tests in/ { sub("s","",$5); print $5 }
    )

Or use another profiling tool to measure 
Installation
------------
Copy the files in `hooks` to the `hooks` directory of a git remote on a
build server (or a local bare repo, which will store the test results).

Running Tests
-------------
Put executable test scripts in the `tests/git-stats` subdirectory of your
project, and make sure to commit them on `master`.
(For consistency, the tests in the current `master` branch are checked out
and run for each branch.)
Simply push to the remote repo, and the `post-receive` hook will automatically
run the tests for any new commits.

Getting Results
---------------
The test results are saved in git `tag`s on the remote,
and each tag has the format `git-stats-XXXXXXX` for a given commit.
Run `git fetch --tags remote` to get all results that have been run so far.

An analysis script, `load-git-stats.py`, is included,
which loads the results from each branch in a Pandas DataFrame.
You can add your custom analysis to this script, or load the results
in any way you want.
If you roll your own analysis, the results can include any type of file
you want, not just simple CSV.
