# macOS (OS X) BUILD NOTES
These notes describe what had to be done on fresh installs of OS X 10.7 - 10.12 in order to compile Armory.

## Requirements / Caveats
At the present time, **it is highly recommended that Armory be compiled on OS X 10.11 with Xcode 7.3.1**. This is due to issues with C++11 support under OS X 10.7, which Armory still supports (although this will change eventually). When compiling using Xcode 8, Xcode forces the minimum supported version to be 10.8. When compiling using Xcode 7 and OS X 10.12, other issues come up. Xcode 7 and OS X 10.11 is the only combo known to produce binaries that run without issues.

Because C++11 support is shaky on OS X 10.7, *Armory developers may not fix bugs found under 10.7*. If a bug is found, please consult the [Bitcoin Forum](https://bitcointalk.org/index.php?board=97.0) or *bitcoin-armory* IRC channel on Freenode for further instructions.

## Instructions
 1. Install the latest version of [Xcode](https://itunes.apple.com/us/app/xcode/id497799835). Due to the XCode 8 issue, you may need to get an [Apple developer account](https://developer.apple.com/) and download the latest XCode 7 version via developer-specific downloads.

 2. Open a terminal and install the Xcode commandline tools. Follow any prompts that appear.

        xcode-select --install

 3. Install and update [Homebrew](http://brew.sh). Warnings can probably be ignored, although environment differences and changes Apple makes to the OS between major releases make it impossible to provide definitive guidance. Any instructions given by Homebrew must be followed. (Exact directions seem to change depending on which version of Xcode is installed.)

        /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
        touch ~/.bashrc
        echo "export CFLAGS=\"-arch x86_64\"" >> ~/.bashrc
        echo "export ARCHFLAGS=\"-arch x86_64\"" >> ~/.bashrc
        source ~/.bashrc
        brew update
        brew doctor

 4. Install and link dependencies required by the Armory build process but not by included Armory binaries.

        brew install python xz swig gettext openssl automake libtool homebrew/dupes/zlib
        brew link gettext --force

 5. Restart your Mac. (This is necessary due to issues related to the Python install.)

 6. Create a symbolic link for glibtoolize. (This requires sudo access and is probably not strictly necessary. It make Autotools much happier, though, and should be harmless otherwise.)

        sudo ln -s /usr/local/bin/glibtoolize /usr/local/bin/libtoolize

 7. Compile Armory.

        cd osxbuild
        python build-app.py > /dev/null

The "> /dev/null" line in step 7 is optional. All this does is prevent the command line from being overwhelmed with build output. The output will automatically be saved to osxbuild/build-app.log.txt no matter what.

Armory.app will be found under the "workspace" subdirectory. It can be moved anywhere on the system, including under `/Applications`.

To avoid runtime issues (e.g. "*ImportError: No module named pkg_resources*") when attempting to run builds on other machines/VMs, make sure $PYTHONPATH is empty. In addition, try not to have any "brew"ed libpng, Python or Qt modules installed. Any of the above could lead to unpredictable behavior.

If you're running a beta version of Xcode, the build tools will need to point to the beta. Open a terminal and run

`sudo xcode-select --switch /Applications/Xcode-Beta.app`

Command line tools should be updated automatically whenever a new version of Xcode is used. However, due to Apple constantly changing requirements for running command line tools, the following command should be run after every Xcode upgrade.

`xcode-select --install`
