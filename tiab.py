#!/usr/bin/env python
###############################################################################
#                                                                             #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                          #
# Distributed under the GNU Affero General Public License (AGPL v3)           #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                        #
#                                                                             #
###############################################################################

# tiab.py is a development tool.
#
# It will start/stop testnet-in-a-box along with armoryd for you.
# You can also call armoryd using this tool and view the logs from armoryd.


import os
import shutil
import subprocess
import sys
import time


def start(args):
    # clean up beforehand
    if os.path.isdir('tiab'):
        shutil.rmtree('tiab')

    # unzip the necessary files
    subprocess.call(['unzip', 'tiabtest/tiab.zip'])

    # start the two bitcoin daemons
    subprocess.call(['bitcoind', '-datadir=tiab/1', '-daemon'] + args)
    subprocess.call(['bitcoind', '-datadir=tiab/2', '-daemon'] + args)

def armoryd(args):
    # start armoryd, log to file
    subprocess.call(
        ['python', 'armoryd.py', '--testnet', '--supernode',
         '--datadir=tiab/armory', '--satoshi-datadir=tiab/1',
         '--satoshi-port=19000', '--satoshi-rpcport=19010',] + args)

def stop(args):
    # if tiab directory doesn't exist, don't do anything
    if not os.path.isdir('tiab'):
        return

    # stop the bitcoin daemons
    subprocess.call(['bitcoin-cli', '-datadir=tiab/1', 'stop'] + args)
    subprocess.call(['bitcoin-cli', '-datadir=tiab/2', 'stop'] + args)

    # stop armoryd
    try:
        call(['stop'])
        time.sleep(3)
    except:
        pass

    # clean up
    shutil.rmtree('tiab')

def armoryqt(args):
    subprocess.call(
         ['python', 'ArmoryQt.py', '--testnet', '--supernode',
          '--datadir=tiab/armory', '--satoshi-datadir=tiab/2',
          '--satoshi-port=19001', '--satoshi-rpcport=19011'] + args)


def call(args):
    if args[0] == 'start':
        armoryd(args[1:])
        return
    subprocess.call(['python', 'armory-cli.py', '--testnet',
                     '--datadir=tiab/armory'] + args)

def usage():
    sys.exit("Usage: %s [start|stop|armoryd|armoryqt|call] <passthrough args>"
             % sys.argv[0])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()

    function = sys.argv[1]
    args = sys.argv[2:]
    if function == 'start':
        start(args)
    elif function == 'stop':
        stop(args)
    elif function == 'armoryd':
        armoryd(args)
    elif function == 'armoryqt':
        armoryqt(args)
    elif function == 'call':
        call(args)
    else:
        usage()
