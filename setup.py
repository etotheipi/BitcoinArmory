#! /usr/bin/python
from distutils.core import setup
import py2exe


opts = {"py2exe":{
    "dll_excludes":["MSWSOCK.dll", "IPHLPAPI.dll", "MSWSOCK.dll", "WINNSI.dll", "WTSAPI32.dll"]
    }}

setup( options = opts, windows = ['../../ArmoryQt.py'])


