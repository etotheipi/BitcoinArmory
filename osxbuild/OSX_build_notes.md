This directory was prepared by forum user "picobit" and reviewed by the ATI team. These notes describe what had to be done on fresh installs of OS X 10.7 (Lion), 10.8 (Mountain Lion), 10.9 (Mavericks), and 10.10 (Yosemite) in order to get build-app.py working.  
Except for the first two steps, all steps are executed from a terminal (aka command line) window.

 1. Install Xcode from Apple's App Store. (It's a free download.)

 2. Run Xcode and install the command-line utilities.  
    "Xcode" --> "Preferences" --> "Downloads"

 3. Open a terminal and run "xcode-select --install". You will have to click through an EULA and possibly other dialogs.

 4. As seen in [Red Emerald's preparation steps for compiling Armory on Mac](https://gist.github.com/WyseNynja/4200620), execute the following steps to install and update brew:
        ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
        touch ~/.bashrc
        echo "export CFLAGS=\"-arch x86_64\"" >> ~/.bashrc
        echo "export ARCHFLAGS=\"-arch x86_64\"" >> ~/.bashrc
        source ~/.bashrc
        brew update
        brew doctor

 5. Execute `brew install xz swig gettext`.

 6. Execute `brew link gettext --force`.

 7. `cd` into the **osxbuild** directory, and execute `python build-app.py`.  
    Armory will be found under the "workspace" subdirectory. Armory.app can be moved elsewhere on the system, including under ``/Applications` so that it's accessible from the OS X Launchpad.


 To avoid runtime issues (e.g. "*ImportError: No module named pkg_resources*") when attempting to run builds on other machines/VMs, make sure $PYTHONPATH is empty. In addition, try not to have any "brew"ed libpng, Python or Qt modules installed. Any of the above could lead to unpredictable behavior.

If running a beta version of Xcode, the build tools will need to point to the beta. Open a terminal and run `sudo xcode-select --switch /Applications/Xcode-Beta.app`. Command line tools should be updated    automatically. If not, follow instructions given when running "clang".
