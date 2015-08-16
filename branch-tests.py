#!/usr/bin/env python

import os
import shutil
import subprocess
import sys
import time

REPO = os.getcwd()
GITROOT = os.path.join(REPO, '.git')
if not os.path.exists(GITROOT):
    GITROOT = REPO
PIDFILE = os.path.join(GITROOT, 'info', 'git-stats.pid')
PID = os.getpid()
while True: # Spinlock while another branch-tests process is running
    if not os.path.exists(PIDFILE):
        with open(PIDFILE, 'w') as pidfh:
            pidfh.write(str(PID))
        # Make sure another process didn't beat us to it
        if open(PIDFILE).read() == str(PID):
            break
    # Spinlock while we're running tests for an old commit
    time.sleep(1)

CLONE = None
try:
    for line in sys.stdin:
        oldref, newref, name = line.strip().split()
        if os.path.dirname(name) != 'refs/heads': # branch ref
            continue
        BRANCH = os.path.basename(name)
        CLONE = tempfile.mkdtemp(prefix='branchtest-%s-' % BRANCH)
        subprocess.check_call(['git', 'clone', '--branch', BRANCH,
                               REPO, CLONE])

        cmd_output = subprocess.check_output(['git', 'reflog'], cwd=CLONE)
        COMMIT = cmd_output.split(' ', 1)[0]

        subprocess.check_call(['git', 'checkout', 'master',
                               '--', 'tests/git-stats'], cwd=CLONE)
        TESTS_PATH = os.path.join(CLONE, 'tests', 'git-analyze')

        output_dir = os.path.join(GITROOT, 'info', 'git-analyze')
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        for test_file in os.path.listdir(TESTS_PATH):
            full_path = os.path.join(TESTS_PATH, test_file)
            try:
                output = subprocess.check_output([full_path], cwd=CLONE)
                commit_dir = os.path.join(output_dir, COMMIT)
                if not os.path.exists(commit_dir):
                    os.mkdir(commit_dir)
                test_name = os.path.splitext(test_file)[0]
                output_path = os.path.join(commit_dir, test_name)
                with open(output_path, 'wb') as output_fh:
                    output_fh.write(output)
            except:
                logging.warn('Test "%s" failed', test_file)

        shutil.rmtree(CLONE)
        CLONE = None
finally:
    os.unlink(PIDFILE)
    if CLONE is not None:
        shutil.rmtree(CLONE)
