# stub
import subprocess
import os
import time
import sys
import shutil
import ast
import fetchInstallers
from release_utils import execAndWait

CLONE_URL = 'https://github.com/etotheipi/BitcoinArmory.git'

verStr   = sys.argv[1]
typeStr  = sys.argv[2]
localDir = sys.argv[3]


fetchInstallers.doFetch()
cloneDir = os.path.join(localDir, 'BitcoinArmory')
rscrDir  = os.path.join(localDir, 'release_scripts')

execAndWait(['git', 'clone', CLONE_URL, cloneDir])
shutil.copytree('../release_scripts', rscrDir)


