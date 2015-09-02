#!/usr/bin/env python

import logging
import os
import shutil
import subprocess
import sys
import tempfile
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

        COMMIT = subprocess.check_output(
            ['git', 'log', '-1', '--format=%h'], cwd=CLONE, env={}).strip()
        MASTER = subprocess.check_output(
            ['git', 'log', '-1', '--format=%h', 'origin/master'], cwd=CLONE,
                env={}).strip()

        # Check out in detached HEAD so we don't commit to the branch
        subprocess.check_call(['git', 'checkout', COMMIT], cwd=CLONE, env={})
        subprocess.check_call(['git', 'checkout', MASTER,
                               '--', 'tests/git-stats'], cwd=CLONE, env={})

        TESTS_PATH = os.path.join(CLONE, 'tests', 'git-stats')
        OUTPUT_DIR = os.path.join(CLONE, 'results', 'git-stats')
        if os.path.exists(OUTPUT_DIR):
                subprocess.check_call(['git', 'rm', '-rf', OUTPUT_DIR],
                                        cwd=CLONE, env={})
        if not os.path.exists(os.path.dirname(OUTPUT_DIR)):
            os.mkdir(os.path.dirname(OUTPUT_DIR))
        if not os.path.exists(OUTPUT_DIR):
            os.mkdir(OUTPUT_DIR)

        SUCCESS = False
        test_files = os.listdir(TESTS_PATH)
        if 'setup' in test_files:
            test_files.remove('setup')
            subprocess.check_call([os.path.join(TESTS_PATH, 'setup')],
                                  cwd=CLONE, env=os.environ)
        for test_file in os.listdir(TESTS_PATH):
            full_path = os.path.join(TESTS_PATH, test_file)
            if not (os.path.isfile(full_path) and os.access(full_path,os.X_OK)):
                continue
            try:
                output = subprocess.check_output([full_path], cwd=CLONE,
                            env=dict(os.environ, PYTHONPATH=CLONE))
            except subprocess.CalledProcessError:
                logging.warn('Test "%s" failed', test_file)
                continue
            test_name = os.path.splitext(test_file)[0]
            output_path = os.path.join(OUTPUT_DIR, test_name)
            with open(output_path, 'wb') as output_fh:
                output_fh.write(output)
            SUCCESS = True

        if SUCCESS:
            subprocess.check_call(['git', 'add', OUTPUT_DIR], cwd=CLONE, env={})
            MSG = 'git-stats tests for commit "%s" (tests from "%s")' % (
                            COMMIT, MASTER)
            AUTHOR = "Git-Stats <empty@example.com>"
            # Repo config
            subprocess.check_call(['git', 'config', 'user.name', 'Git Stats'],
                                  cwd=CLONE, env={})
            subprocess.check_call(['git', 'config', 'user.email', 'test@example.com'],
                                  cwd=CLONE, env={})
            subprocess.check_call(['git', 'commit', '-m', MSG],
                                    cwd=CLONE, env={})

            # More compact, easy-to-parse message
            TAG_MSG = 'git-stats:%s:%s' % (COMMIT, MASTER)
            TAG_NAME = 'git-stats_%s_%s' % (COMMIT, MASTER)
            subprocess.check_call(['git', 'tag', '-a', '-m', TAG_MSG, TAG_NAME],
                                  cwd=CLONE, env={})

            subprocess.check_call(['git', 'push', '--tags', 'origin'],
                                  cwd=CLONE, env={})

        shutil.rmtree(CLONE)
        CLONE = None
finally:
    os.unlink(PIDFILE)
    if CLONE is not None:
        shutil.rmtree(CLONE)
