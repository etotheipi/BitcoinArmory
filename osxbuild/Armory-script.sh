#!/bin/bash
# This is the initial driver script executed by the Armory application on OS X.
# Its role is to set up the environment before passing control to Python.

# Set environment variables so the Python executable finds its stuff.
# Note that `dirname $0` doesn't always work. What's here is more robust.
DIRNAME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ARMORYDIR="$DIRNAME/py/lib/armory"
LIBDIR="$DIRNAME/../Dependencies"
FRDIR="$DIRNAME/../Frameworks"

export PYTHONPATH="$ARMORYDIR"
export DYLD_LIBRARY_PATH="${LIBDIR}:${FRDIR}"
export DYLD_FRAMEWORK_PATH="${LIBDIR}:${FRDIR}"

# OS X chokes if you try to pass command line args when none exist. Pass only
# if there are args to pass. 10.7 (Lion) also has a quirk where $#=1 if there
# are no args. Adjust for it in order for Armory to run. Unfortunately, there
# seems to be no good way to pass args in 10.7, as $#=1 when there's 1 arg!
# Users can work around this by passing multiple args.
OSXVER=`sw_vers -productVersion | awk '{ print substr( $0, 0, 4 ) }'`
if [ $# == "0" ]; then
	$DIRNAME/Python $ARMORYDIR/ArmoryQt.py
elif [ $# == "1" -a $OSXVER == "10.7" ]; then
	$DIRNAME/Python $ARMORYDIR/ArmoryQt.py
else
	$DIRNAME/Python $ARMORYDIR/ArmoryQt.py "$@"
fi
