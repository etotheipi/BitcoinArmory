#!/bin/bash
# This is the initial driver script executed by the Armory application on OS X.
# Its role is to set up the environment before passing control to Python.

# Set environment variables so the Python executable finds its stuff.
# Note that `dirname $0` gives a relative path. We'd like the absolute path.
DIRNAME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ARMORYDIR="$DIRNAME/py/usr/lib/armory"
LIBDIR="$DIRNAME/../Dependencies"
FRDIR="$DIRNAME/../Frameworks"

export PYTHONPATH="$ARMORYDIR"
export DYLD_LIBRARY_PATH="${LIBDIR}:${FRDIR}"
export DYLD_FRAMEWORK_PATH="${LIBDIR}:${FRDIR}"

# OS X chokes if you try to pass command line args when none exist. Pass only
# if there are args to pass.
#OSXVER=`sw_vers -productVersion | awk '{ print substr( $0, 0, 4 ) }'`
if [ $# == "0" ]; then
	$FRDIR/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python $ARMORYDIR/ArmoryQt.py "$@"
else
	$FRDIR/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python $ARMORYDIR/ArmoryQt.py "$@"
fi
