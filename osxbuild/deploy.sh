#!/bin/bash

# We will actually won't be signing on this computer.
#CERTIFICATE="None"

function clean()
{
    echo "Removing previous installation..."
    # delete env and app
    sudo rm -rf Armory.app env
}

function get_dependencies()
{
    # get build dependencies
    echo "Installing dependencies..."
    brew install cryptopp swig qt pyqt wget
    sudo pip install virtualenv 
    sudo pip install psutil
}

function make_env()
{
    echo "Making python environment..."
    virtualenv -q env
    cd env
    bin/pip install twisted >/dev/null
    bin/pip install psutil 

    # move global pyqt into the env
    # do sip first
    cp -r /usr/local/Cellar/sip/4.*/lib/python2.*/site-packages/ lib/python2.*/site-packages/
    cp -r /usr/local/Cellar/sip/4.*/include/ include/
    cp -r /usr/local/Cellar/sip/4.*/bin/ bin/
    # now pyqt
    cp -r /usr/local/Cellar/pyqt/4.*/lib/python2.*/site-packages/PyQt4 lib/python2.*/site-packages/
    cp -r /usr/local/Cellar/pyqt/4.*/share/ share/
    cp -r /usr/local/Cellar/pyqt/4.*/bin/ bin/
    cd ..
}

function make_app()
{
    echo "Creating Armory.app..."
    mkdir -p Armory.app/Contents/Dependencies
    mkdir -p Armory.app/Contents/Resources
    # insert python
    cp -r env Armory.app/Contents/MacOS
    # insert qt frameworks
    cp -r /usr/local/lib/QtCore.framework Armory.app/Contents/Dependencies/QtCore.framework
    cp -r /usr/local/lib/QtGui.framework Armory.app/Contents/Dependencies/QtGui.framework
    cp /usr/local/lib/libpng15.15.dylib Armory.app/Contents/Dependencies/libpng15.15.dylib

    # essential .app stuff
    cp Armory Armory.app/Contents/MacOS/Armory
    chmod +x Armory.app/Contents/MacOS/Armory
    cp Info.plist Armory.app/Contents/Info.plist
    cp ../img/armory_icon_fullres.icns Armory.app/Contents/Resources/Icon.icns
}

function build_armory()
{
    echo "Building Armory..."
    cd .. # root dir
    make >/dev/null # keeping stderror
    python -m py_compile *.py  # compile to pyc
    python -m py_compile jsonrpc/*.py  # compile to pyc

    echo "Moving Armory to app..."
    mkdir -p osxbuild/Armory.app/Contents/MacOS/armorybuild
    # osxbuild has to be excluded, otherwise there will be recursion hell
    # plus some other stuff has to be removed, so let's use this huge thing
    tar cf - --exclude=osxbuild --exclude=cppForSwig --exclude=dpkgfiles --exclude=extras \
    --exclude=windowsbuild --exclude=*.txt --exclude=.git --exclude=.gitignore --exclude=*.py --exclude=Makefile \
     * 2>&1 | (cd osxbuild/Armory.app/Contents/MacOS/armorybuild && tar xvf -) >/dev/null 2>&1
    cd osxbuild
}

function finish()
{
    # codesign -s $CERTIFICATE Armory.app
    rm -rf Armory.app/Contents/MacOS/lib/python2.*/lib-dynload
    rm -rf Armory.app/Contents/MacOS/lib/python2.*/config
    rm -rf Armory.app/Contents/MacOS/lib/python2.*/encodings
}

cd "${0%/*}"

get_dependencies

if [ ! -d env ];
then
    make_env
fi

if [ ! -d Armory.app ];
then
    make_app
fi

build_armory
finish
