# macOS BUILD NOTES
These notes describe what had to be done on fresh installs of macOS 10.8 - 10.13 in order to compile Armory.

## Requirements / Caveats
Armory is designed to run only on macOS 10.8 or later. Running on 10.7 may be possible with proper code editing. However, this isn't recommended due to [issues with C++11 support under macOS 10.7](https://github.com/bitcoin/bitcoin/issues/8577#issuecomment-255945996). The latest versions of macOS and Xcode that can compile 10.7-compatible binaries are macOS 10.11 and Xcode 7.3.1. (The binaries are also compatible with macOS 10.12 and beyond.) An [Apple developer account](https://developer.apple.com/) may be used to obtain Xcode 7.3.1.

If a bug is found, please consult the [Bitcoin Forum](https://bitcointalk.org/index.php?board=97.0) or *bitcoin-armory* IRC channel on Freenode for further instructions.

## Instructions
 1. Get an Apple developer account (free), log in, and download the latest version of Command Line Tools for Xcode. As an alternative, install the latest version of [Xcode](https://itunes.apple.com/us/app/xcode/id497799835) and download Command Line Tools via Xcode. Either choice will be updated via the App Store.

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

        brew install xz swig gettext openssl automake libtool homebrew/dupes/zlib
        brew link gettext --force

 5. Restart your Mac. (This is necessary due to issues related to the Python install.)

 6. Create a symbolic link for glibtoolize. (This requires sudo access and is probably not strictly necessary. It make Autotools much happier, though, and should be harmless otherwise.)

        sudo ln -s /usr/local/bin/glibtoolize /usr/local/bin/libtoolize

 7. Download Armory [here](https://github.com/goatpig/BitcoinArmory). There are two options.

   7.1. Download the source code from the [GitHub Armory releases page](https://github.com/goatpig/BitcoinArmory/releases/). Ensure that you download **only** the relevant "src.tar.gz" file, and **not** the code from the "Download ZIP" buttonfound elsewhere on GitHub. (Long story short, the `fcgi` submodule, which Armory requires, will **only** be included in the "src.tar.gz" file due to a long-standing GitHub bug affecting code auto-downloads.) After verifying the code, per the [macOS README directions](../README_macOS.md), unzip the code.

   7.2. The more advanced method, which is recommended only for developers and other advanced tinkerers, is to use [Git version control](https://en.wikipedia.org/wiki/Git) in order to obtain the code. While more advanced, this makes it far easier to obtain code updates and to submit patches to Armory. Go [here](https://github.com/goatpig/BitcoinArmory) and use the "Clone or download" button to get a URL to use to clone the code. [This page](https://help.github.com/articles/cloning-a-repository-from-github/) has a partial tutorial, and [SourceTree](https://www.sourcetreeapp.com/) is a good app for starters. It is highly recommended that, at a bare minimum, users learn how to clone a repo and successfully switch between branches before going any further.

 8. (*OPTIONAL*) If compiling on a pre-10.12 macOS version with the intention of compiling for macOS 10.7, change the minimum version to 10.7 from 10.8 in osxbuild/build-app.py, osxbuild/objc\_armory/ArmoryMac.pro, and osxbuild/qmake\_LFLAGS.patch by searching for instances of 10.8 and changing them to 10.7.

 9. Compile Armory.

        cd *Location of Armory source code*  (An example would be ~/Projects/BitcoinArmory)
		git submodule init  (Required only if using Git version control, as discussed in Step 7.2.)
		git submodule update  (Required only if using Git version control, as discussed in Step 7.2.)
		cd osxbuild
        python build-app.py > /dev/null

The "> /dev/null" line in step 9 is optional. All this does is prevent the command line from being overwhelmed with build output. The output will automatically be saved to osxbuild/build-app.log.txt no matter what.

Armory.app will be found under the "workspace" subdirectory. It can be moved anywhere on the system, including under `/Applications`.

To avoid runtime issues (e.g. *ImportError: No module named pkg_resources*) when attempting to run builds on other machines/VMs, make sure $PYTHONPATH is empty. In addition, try not to have any "brew"ed libpng, Python or Qt modules installed. Any of the above could lead to unpredictable behavior.

## Compilation issues
If you run into any compilation issues, please [post on Bitcoin Forum's Armory subforum](https://bitcointalk.org/index.php?board=97.0) or consult the *bitcoin-armory* IRC channel on Freenode. Note that compilation of "dev"/"testing" versions of Armory may be broken on Linux and macOS. Armory's developed primarily for Windows, with Linux and macOS compilation issues fixed once goatpig's satisfied with the state of the Windows code. The "master" code should never be broken, as it consists of what gets officially released.
