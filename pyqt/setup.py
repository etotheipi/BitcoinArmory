#! /usr/bin/python
from distutils.core import setup
import py2exe


setup( windows = ['../pyqt/blockexplore.pyw'] )
   #options = {'py2exe': {'bundle_files': 1}}, \
   #zipfile = None )

