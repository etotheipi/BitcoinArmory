#! /usr/bin/python
from distutils.core import setup
import py2exe


setup( windows = ['../ArmoryQt.py'] )
   #options = {'py2exe': {'bundle_files': 1}}, \
   #zipfile = None )

