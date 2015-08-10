#!/usr/bin/env python

import os
import shutil
import subprocess
import sys
import time

REPO = os.getcwd()
GITROOT = os.path.join(REPO, 'git')
if not os.path.exists(GITROOT):
    GITROOT = REPO
PIDFILE = os.path.join(GITROOT, 'info', 'git-branch-tests.pid')
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
        subprocess.check_output(['git', 'clone', '--branch', BRANCH,
                                 REPO, CLONE])
        shutil.rmtree(CLONE)
        CLONE = None
finally:
    os.unlink(pidfh)
    if CLONE is not None:
        shutil.rmtree(CLONE)
