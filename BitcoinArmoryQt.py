#! /usr/bin/python
################################################################################
#
# Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
#
# Project:    BitcoinArmory          (https://github.com/etotheipi/BitcoinArmory)
# Author:     Alan Reiner
# Orig Date:  20 November, 2011
# Descr:      This file serves as an engine for python-based Bitcoin software.
#             I forked this from my own project -- PyBtcEngine -- because I
#             I needed to start including/rewriting code to use CppBlockUtils
#             but did not want to break the pure-python-ness of PyBtcEngine.
#             If you are interested in in a pure-python set of bitcoin utils
#             please go checkout the PyBtcEngine github project.
#
#
################################################################################

import hashlib
import random
import time
import os
import sys
import shutil
import math
from datetime import datetime

# 8000 lines of python to help us out...
from btcarmoryengine import *

from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet.defer import Deferred

# This is an amazing trick for create enum-like dictionaries. 
# Either automatically numbers (*args), or name-val pairs (**kwargs)
#http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)






if __name__ == '__main__':
   app = QApplication(sys.argv)
   import qt4reactor
   qt4reactor.install()




