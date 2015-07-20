#! /usr/bin/python
from __future__ import print_function
import subprocess
import sys
import os

_BIN_PATH = os.path.dirname(sys.executable)

def _cmd(cmd):
    cmd = "{0}/{1}".format(_BIN_PATH, cmd)
    print("+", cmd, file=sys.stderr)
    subprocess.check_call(cmd, shell=True)

if __name__ == '__main__':
    cmd = "py.test tests --cov=chords --cov-report=html"
    if '--parallel' in sys.argv:
        cmd += ' -n 4'
    try:
        _cmd(cmd)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
