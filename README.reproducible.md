#Armory Reproducible Build Documentation

##Introduction

Gitian is just one method for achieving reproducible builds. Armory uses Gitian
for OS X and Windows, but uses the Debian Reproducible Build Toolchain for
Debian packages. Armory does not support the RPM builds, but provides
instructions for doing RPM builds.

##Gitian

Gitian is the build system that Bitcoin Core uses for reproducible builds.
Armory has adopted it for OS X and Windows reproducible builds. This guide
assumes you are using KVM as the virtualization technology to make the VMs
that Gitian uses to build in, but gitian-tools also supports LXC.

The following steps will allow you to build Armory reproducibly using Gitian.

1. Obtain gitian-tools from [Devrandom's GitHub][Devrandom's GitHub].
2. Run `bin/make-base-vm --suite trusty`. Armory uses Ubuntu Trusty as the OS
   of the VM to build in. Add `--lxc` if using LXC.
3. If using LXC, run `export USE_LXC=1`.
4. Run `bin/gbuild --commit BitcoinArmory=autotools-gitian ../BitcoinArmory/gitian-descriptors/bitcoin-armory-osx.yml`. The commit option is optional and
   specifies a Git tag, branch name, or commit hash. By default it is master.
   The command ends with the path to the appropriate YAML file in the Armory
   source tree. In this case, the OS X Gitian descriptor is used to indicate
   that we want to build for OS X.
5. TODO: Include instructions about signing and verifying.

Note that the OS X build requires you have the Mac SDK. See
[fetch and build inputs][fetch and build inputs].

Note that you may (read will) need to grab the dependency sources manually. See
[seed cache][seed cache]. Just replace bitcoin in the instructions with
BitcoinArmory or whatever your Armory source tree is named.

##Linux

###Reproducible

For Linux reproducible builds, we have used the
[Debian Reproducible Build Toolchain][Debian Toolchain]. We have found the
toolchain to be better suited to producing reproducible Debian packages simply
due to the fact that it was designed specifically with Debian packages in mind.

For more on producing a reproducible Debian package of Armory, read
[dpkgfiles/make\_deb\_package.README](dpkgfiles/make_deb_package.README)

###Non-reproducible

If you don't want to build for Linux reproducibly, or you are building for a
system that does not support deb or rpm packages, you can just build using the
Autotools-based system directly. This has only been tested when building on
Linux.

    cd path-to-armory-source
    ./autogen.sh
    ./configure # don't need to specify host if building on same architecture as host
    make
    make install # optional

Specify `--host x86_64-linux-gnu` or `--host i686-linux-gnu` if you are
building for 64-bit from a 32-bit machine or building 32-bit from a 64-bit
machine respectively.

If you don't run `make install`, you can just run `python ArmoryQt.py` from the
Armory source tree. If you run `make install`, you should have `armory` on your
path. So you can just run `armory`.

###Fedora Package (RPM)

RPM packages are not officially supported. They are a convenience to users.
Read [rpmfiles/armory.spec.README](rpmfiles/armory.spec.README) for more info.

##Raspberry Pi

###Reproducible

The Raspberry Pi reproducible build system uses Gitian. Refer to the Gitian
instructions and use gitian-descriptors/bitcoin-armory-raspi.yml as the Gitian
descriptor.

###Non-reproducible

First, make sure the the [Raspberry Pi toolchain][Raspberry Pi toolchain] is
on your PATH. The specific path from that repository that you should add to
your PATH is `arm-bcm2708/gcc-linaro-arm-linux-gnueabihf-raspbian-x64/bin`.
Then follow the Linux instructions, but use `--host arm-linux-gnueabihf` when
calling the configure script.

#FUTURE DIRECTIONS (DO NOT USE)

##OS X

###Reproducible

The OS X reproducible build system uses Gitian. Refer to the Gitian
instructions and use gitian-descriptors/bitcoin-armory-osx.yml as the Gitian
descriptor.

###Non-reproducible

You can use the Autotools-based build system to build Armory.app. This has been
tested on OS X and Linux as the build machines.

For OS X:

    cd path-to-armory-source
    ./autogen.sh
    ./configure
    make Armory.app

For Linux:

    # install cctools-port (https://github.com/theuni/cctools-port)
    echo -e '#!/bin/sh\nexit 0' > /usr/local/bin/x86_64-apple-darwin11-dsymutil
    mv /usr/local/bin/x86_64-apple-darwin11-ld /usr/bin/
    cd path-to-armory-source
    ./autogen.sh
    ./configure --host=x86_64-apple-darwin11 \
                --with-osx-sdk-path=/usr/share/MacOSX10.9.sdk
    make Armory.app

In either case, you should be left with an Armory.app in osxbuild that will run
on OS X 10.7+.

Alternatively, you can just run `make` if you don't want to build Armory.app.

Note that Armory.app currently builds with Python 3 and Qt 5, but Armory still
uses Python 2 and Qt 4. Therefore, the user needs to install Qt 4 before
Armory.app will run.

##Windows

###Reproducible

The new reproducible build system does not currently support Windows builds.
Work is being done to make a single static exe that includes everything needed
to run Armory on a Windows machine without requiring the end use to install
Python or anything else. Just double-click on the exe and Armory pops up.

###Non-reproducible

If you just want to build a non-reproducible version of Armory for Windows, you
can do so using the new Autotools-based build system. It has only been tested
from Linux, but should work from any system as long as you have the proper
toolchain installed. Run the following commands:

    sudo apt-get install mingw-w64 # For Debian-based distros; adjust as appropriate
    cd path-to-armory-source
    ./autogen.sh
    ./configure --host x86_64-w64-mingw32 # replace x86_64 with i686 for 32-bit
    make

You may need to install build dependencies if the configure script finishes
with errors. After installing the build dependencies, rerun the configure
script.

The build dependencies you may potentially need are python3
(python3 package in Debian), swig (swig package in Debian), and
pyrcc5 (pyqt5-dev-tools package in Debian).

You can also get downloads from the following URLs:

* [python3](https://www.python.org/downloads/)
* [swig](http://www.swig.org/download.html)
* [pyrcc5 (as part of PyQt5)](http://www.riverbankcomputing.com/software/pyqt/download5)

At this point, you should have a \_CppBlockUtils.pyd file in the root of the
Armory source tree. You should be able to transfer the entire source tree over
to a Windows machine and run `python ArmoryQt.py` from the command window as
long as you have all the dependencies installed, such as Python.

[Devrandom's GitHub]: https://github.com/devrandom/gitian-builder
[fetch and build inputs]: https://github.com/bitcoin/bitcoin/blob/master/doc/release-process.md#fetch-and-build-inputs-first-time-or-when-dependency-versions-change
[seed cache]: https://github.com/bitcoin/bitcoin/blob/master/doc/release-process.md#optional-seed-the-gitian-sources-cache
[Debian Toolchain]: https://wiki.debian.org/ReproducibleBuilds/ExperimentalToolchain
[Raspberry Pi toolchain]: https://github.com/raspberrypi/tools
