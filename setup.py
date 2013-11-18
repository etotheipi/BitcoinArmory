#! /usr/bin/python
from distutils.core import setup
import py2exe


opts = {"py2exe":{
    "dll_excludes":["MSWSOCK.dll", "IPHLPAPI.dll", "MSWSOCK.dll", "WINNSI.dll", "WTSAPI32.dll"],
    "bundle_files": 1
    }}

setup( options = opts, windows = ['../../ArmoryQt.py'], zipfile = None )

   #options = {'py2exe': {'bundle_files': 1}}, \
   #zipfile = None )


