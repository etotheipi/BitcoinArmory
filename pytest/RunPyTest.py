#!/usr/bin/env python

import sys
import subprocess


# ...
# the rest of your module's code
# ...

if __name__ == '__main__':
   if len(sys.argv) > 1:
      for module in sys.argv[1:]:
         subprocess.call([sys.executable, '-m', 'unittest', 'discover', '.',  module+'.py'])
   else:
      subprocess.call([sys.executable, '-m', 'unittest', 'discover', '.', '*Test.py'])