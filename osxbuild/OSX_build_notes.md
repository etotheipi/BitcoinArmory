These notes describe what had to be done on fresh installs of OS X 10.7 - 10.11 in order to compile Armory.

 1. Install [Xcode](https://itunes.apple.com/us/app/xcode/id497799835)

 2. Open a terminal and install the Xcode commandline tools.

    `xcode-select --install`

 3. Install [Homebrew](http://brew.sh) and update Homebrew:

        /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
        touch ~/.bashrc
        echo "export CFLAGS=\"-arch x86_64\"" >> ~/.bashrc
        echo "export ARCHFLAGS=\"-arch x86_64\"" >> ~/.bashrc
        source ~/.bashrc
        brew update
        brew doctor

 4. Install dependencies:

    `brew install xz swig gettext`

    `brew link gettext --force`

 5. Move into the osxbuild directory and run build-app.py

    `cd osxbuild`

    `python build-app.py`

Armory will be found under the "workspace" subdirectory.
Armory.app can be moved anywhere on the system, including under ``/Applications`.

To avoid runtime issues (e.g. "*ImportError: No module named pkg_resources*") when attempting to run builds on other machines/VMs, make sure $PYTHONPATH is empty. In addition, try not to have any "brew"ed libpng, Python or Qt modules installed. Any of the above could lead to unpredictable behavior.

If you're running a beta version of Xcode, the build tools will need to point to the beta.
Open a terminal and run

`sudo xcode-select --switch /Applications/Xcode-Beta.app`

Command line tools should be updated automatically. If not, follow instructions given when running "clang".
