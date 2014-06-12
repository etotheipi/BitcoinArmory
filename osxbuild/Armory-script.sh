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

# Misc. crap to keep around in case it's ever needed.
#OSXVER=`sw_vers -productVersion | awk '{ print substr( $0, 0, 4 ) }'`
#if [ $# == "0" ]; then # <-- If 0 CL args....

# Call ArmoryQt and get this party started!
"$FRDIR/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python" "$ARMORYDIR/ArmoryQt.py" "$@"
