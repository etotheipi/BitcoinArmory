#!/bin/bash
# This is the initial driver script executed by the Armory application on OS X.
# Its role is to set up the environment before passing control to Python.
# NB: If any changes are made to this script, you'll probably need to make the
# same changes to the armoryd script.

# Set environment variables so the Python executable finds its stuff.
# Note that `dirname $0` gives a relative path. We'd like the absolute path.
DIRNAME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ARMORYDIR="${DIRNAME}/py/usr/local/lib/armory"
LIBDIR="${DIRNAME}/../Dependencies"
FRDIR="${DIRNAME}/../Frameworks"

export PYTHONPATH="$ARMORYDIR"
export DYLD_LIBRARY_PATH="${LIBDIR}:${FRDIR}"
export DYLD_FRAMEWORK_PATH="${LIBDIR}:${FRDIR}"

# Misc. crap to keep around in case it's ever needed.
#OSXVER=`sw_vers -productVersion | awk '{ print substr( $0, 0, 4 ) }'`
#if [ $# == "0" ]; then # <-- If 0 CL args....

# OS X has a quirk. For whatever reasons, if you execute Python from a different
# location than the location of what actually gets executed when you run Armory,
# the menu bar calls Armory "Python". However, if you symlink Python and run the
# symlink from the execution directory, the app name from Info.plist is used.
# Also, the link should be here so that the link works wherever this is
# executed, and not just on the build machine.
ln -sf "${FRDIR}/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python" "${DIRNAME}/Python"

# Assume all args are meant for Armory. Assuming otherwise, for shell scripts
# at least, it horribly painful.
exec "${DIRNAME}/Python" "${ARMORYDIR}/ArmoryQt.py" "$@"
