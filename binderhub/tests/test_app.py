"""Exercise the binderhub entrypoint"""

from subprocess import check_output
import sys

def test_help():
    check_output([sys.executable, '-m', 'binderhub', '-h'])

def test_help_all():
    check_output([sys.executable, '-m', 'binderhub', '--help-all'])

