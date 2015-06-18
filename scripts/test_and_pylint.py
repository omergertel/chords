#! /usr/bin/python
from __future__ import print_function
import subprocess
import sys
import os

_OLD_PYTHON = sys.version_info[0] == 2 and sys.version_info[1] <= 6
_PYPY = hasattr(sys, "pypy_version_info")
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
        if not (_PYPY or _OLD_PYTHON):
            _cmd("pylint --rcfile=.pylintrc setup.py")
            _cmd("pylint --rcfile=.pylintrc chords")
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
