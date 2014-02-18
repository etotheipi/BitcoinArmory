#!/bin/bash
# This is the initial driver script executed by the Armory application on OS X.
# Its role is to set up the environment before passing control to Python.
# WARNING: For unknown reasons, OS X seems to be very touchy about whether or
# not the program will run if you double-click it, or use "open -a" on it. You
# may have to manually invoke this script in order to run Armory.

# Set environment variables so the Python executable finds its stuff.
# Note that `dirname $0` doesn't always work. This gives the absolute path.
DIRNAME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ARMORYDIR="$DIRNAME/py/lib/armory"
LIBDIR="$DIRNAME/../Dependencies"
FRDIR="$DIRNAME/../Frameworks"

export PYTHONPATH="$ARMORYDIR"
export DYLD_LIBRARY_PATH="${LIBDIR}:${FRDIR}"
export DYLD_FRAMEWORK_PATH="${LIBDIR}:${FRDIR}"

# OS X chokes if you try to pass command line args when none exist. Pass only
# if there are args to pass.
OSXVER=`sw_vers -productVersion | awk '{ print substr( $0, 0, 4 ) }'`
if [ $# == "0" ]; then
	$DIRNAME/Python $ARMORYDIR/ArmoryQt.py
else
	$DIRNAME/Python $ARMORYDIR/ArmoryQt.py "$@"
fi
