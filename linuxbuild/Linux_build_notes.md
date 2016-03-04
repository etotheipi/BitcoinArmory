# Building Armory From Source

Non-Debian-based Linux users will have to compile from source.

Compiling in Linux has proven to be quite easy. There are only a few dependencies, and they are all versionless, so there are no games you have to play with system library versions in order to get it to work.

## Verifying Source Code Authenticity

The latest stable version of Armory is always be tagged in the git repository by its version number.

Versions up to 0.93.3 are signed with the Alan Reiner's Armory signing key ([98832223](https://pgp.mit.edu/pks/lookup?op=vindex&search=0x4AB16AEA98832223)).
Versions 0.94 and later are signed with goatpig's key (4922589A)

Here’s how to import the Armory signing key into your keyring from the Ubuntu keyserver and verify the signature using `git tag -v`:

```
$ gpg --recv-keys --keyserver keyserver.ubuntu.com 98832223
gpg: requesting key 98832223 from hkp server keyserver.ubuntu.com
gpg: key 98832223: public key "Alan C. Reiner (Armory Signing Key) <alan.reiner@gmail.com>"

$ git tag -v v0.93.3
tag v0.93.3
tagger Armory Technologies, Inc <contact@bitcoinarmory.com> 1424537423 -0500
gpg: Signature made Sat 21 Feb 2015 11:50:23 AM EST using RSA key ID 98832223
gpg: Good signature from "Alan C. Reiner (Offline Signing Key) <alan@bitcoinarmory.com>"
```

The above example is specifically for checking the tag for version 0.93.3. You can replace it with the latest version number posted on our website. To view all tags from Armory’s Github page, click on the button that says `branch: master` and then select the “tags” tab. All major releases are accompanied by a signed tag.

## Building in Linux

To checkout and build a specific version, simply use `git checkout tag` before the `make` command in the build instructions below. For instance, to build version 0.93.3, you would simply do:

```
$ git checkout v0.93.3
Note: checking out 'v0.93.3'
...
HEAD is now at e59e10d... Add comment explaining why the padding was removed
```

### Ubuntu Build Instructions

In Ubuntu, you are required to install some packages before attempting to build Armory. To do so, type the following line (omitting the dollar sign) into a terminal. This only needs to be done once:

    $ sudo apt-get install git-core build-essential pyqt4-dev-tools swig libqtcore4 libqt4-dev python-qt4 python-dev python-twisted python-psutil

Now, you need to clone Armory's git repository:

    $ git clone https://github.com/goatpig/BitcoinArmory.git
    $ cd BitcoinArmory

At this point, you may want to check the authenticity of the source code, as stated above. You can do that by typing the following (replacing `0.93.1` with the latest Armory version):

    $ git checkout v0.93.1
    $ git tag -v v0.93.1

Finally, we make the application. This may take a while, depending on your computer:

    $ make

You're all set! To launch Armory, type in a terminal in the BitcoinArmory directory:

    $ python ArmoryQt.py

You can also run `sudo make install` after building, which will install Armory system-wide. This will allow you to launch it from the Applications –> Internet menu.


### Arch Build Instructions

You can get Armory from the Arch User Repository.

First, visit [this AUR page](https://aur.archlinux.org/packages/armory-git/) and click 'Download snapshot' on the right hand side.  
Save the archive, then open a terminal and type (omitting the dollar sign):

    $ tar -xvf armory-git.tar.gz
    $ cd armory-git

Now, open the individual files using a text editor and verify that they don't do anything malicious.

Finally, make and install Armory:

    $ makepkg -sri

You're all set! You can find Armory in your "Applications" menu. You can also launch it by typing `armory` in a terminal.
