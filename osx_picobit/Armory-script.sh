#!/bin/bash

# This is the initial driver script being executed by the Armory application on Mac OS.
# Its role is to set up the environment before passing control onto Python.

DIRNAME="`dirname $0`"
ARMORYDIR="$DIRNAME/py/usr/lib/armory"
LIBDIR="$DIRNAME/../Dependencies"
FRDIR="$DIRNAME/../Frameworks"

# Set environment variables so the Python executable finds its stuff.
export PYTHONPATH="$ARMORYDIR"
export DYLD_LIBRARY_PATH="${LIBDIR}:${FRDIR}"
export DYLD_FRAMEWORK_PATH="${LIBDIR}:${FRDIR}"

$DIRNAME/Python $ARMORYDIR/ArmoryQt.py