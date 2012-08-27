#!/usr/bin/env python
import sys
from setuptools import setup

try:
    cmd = sys.argv[1]
except IndexError:
    print 'Usage: setup.py install|py2exe|py2app|cx_freeze'
    raise SystemExit

if cmd == 'py2exe':
    import py2exe

    setup( windows = ['../ArmoryQt.py'] )

elif cmd == 'py2app':
    import py2app

    APP = ['ArmoryQt.py']
    DATA_FILES = []
    OPTIONS = {'argv_emulation': False}

    setup(
        app=APP,
        data_files=DATA_FILES,
        options={'py2app': OPTIONS},
        setup_requires=['py2app'],
    )

