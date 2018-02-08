# Building Armory From Source

Non-Debian-based Linux users will have to compile from source.

Compiling in Linux has proven to be quite easy. There are only a few dependencies, and they are all versionless, so there are no games you have to play with system library versions in order to get it to work.

## Verifying Source Code Authenticity

The latest stable version of Armory is always be tagged in the git repository by its version number, and signed with the [Armory signing key (4922589A)](http://keyserver.ubuntu.com/pks/lookup?search=goatpig). For releases 0.93.3 and earlier, the [old Armory signing key (98832223)](http://keyserver.ubuntu.com/pks/lookup?search=Alan+Reiner) was used.

Here’s how you download the Armory signing key directly into your keyring from the Ubuntu keyserver, and then verify the signature using `git tag -v`:

~~~ bash
$ gpg --recv-keys --keyserver keyserver.ubuntu.com 4922589A
gpg: requesting key 4922589A from hkp server keyserver.ubuntu.com
gpg: key 4922589A: public key "goatpig (Offline signing key for Armory releases) <moothecowlord@gmail.com>" imported
$ git tag -v v0.96
object a3d01aa72293f82c3ef3f1d29f93c83ad70099f4
type commit
tag v0.96
tagger goatpig <moothecowlord@gmail.com> 1493581585 +0200

v0.96
gpg: Signature made Sun 30 Apr 2017 03:46:25 PM EDT using RSA key ID 4922589A
gpg: Good signature from "goatpig (Offline signing key for Armory releases) <moothecowlord@gmail.com>"
~~~


The above example is specifically for checking the tag for version "v0.96", which may not be the latest version by the time you are reading these instructions.  You can replace it with the latest version number posted on our website. All releases can be viewed on the [github releases page](https://github.com/goatpig/BitcoinArmory/releases). All major releases are accompanied by a signed tag.

## Building in Linux

To checkout and build a specific version, simply use `git checkout tag` before the `make` command in the build instructions below. For instance, to build version 0.96, you would simply use:

~~~ bash
$ git checkout v0.96
Note: checking out 'v0.96'.
...
HEAD is now at a3d01aa... bump version
~~~

### Ubuntu Build Instructions

In Ubuntu, you are required to install some packages before attempting to build Armory. To do so, type the following line (omitting the dollar sign) into a terminal. This only needs to be done once:

    $ sudo apt-get install git-core pkg-config build-essential pyqt4-dev-tools swig libqtcore4 libqt4-dev python-qt4 python-dev python-twisted python-psutil

Now, you need to clone Armory's git repository and initialize the submodules:

~~~bash
$ git clone https://github.com/goatpig/BitcoinArmory.git
$ cd BitcoinArmory
$ git submodule init
$ git submodule update
~~~

At this point, you may want to check the authenticity of the source code, as stated above. You can do that by typing the following (replacing `0.93.1` with the latest Armory version):

~~~bash
$ git checkout v0.96
$ git tag -v v0.96
~~~

Init and update submodules; this will check out external repositories withing Armory source tree

~~~bash
    $ git submodule init
    $ git submodule update
~~~

Finally, we make the application. This may take a while, depending on your computer:

~~~bash
$ ./autogen.sh
$ ./configure
$ make
~~~

You're all set! To launch Armory, type in a terminal in the BitcoinArmory directory:

~~~bash
$ python ArmoryQt.py
~~~

You can also run `sudo make install` after building, which will install Armory system-wide. This will allow you to launch it from the Applications –> Internet menu.


### Arch Build Instructions

You can get Armory from the Arch User Repository.

First, visit [this AUR page](https://aur.archlinux.org/packages/armory-git/) and click 'Download snapshot' on the right hand side.  
Save the archive, then open a terminal and type (omitting the dollar sign):

~~~bash
$ tar -xvf armory-git.tar.gz
$ cd armory-git
~~~

Now, open the individual files using a text editor and verify that they don't do anything malicious.

Finally, make and install Armory:

~~~bash
$ makepkg -sri
~~~

You're all set! You can find Armory in your "Applications" menu. You can also launch it by typing `armory` in a terminal.
