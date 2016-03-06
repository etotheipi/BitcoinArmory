# RASPBERRY PI CROSS-COMPILATION INSTRUCTIONS
Armory may be run on the Raspberry Pi computer, both in online and offline mode (although offline is highly recommended due to strain placed on hardware by the online mode.) The following set of commands, run from the Armory root directory, will execute the build script. A setup location is optional and will default to the *r-pi* subdirectory inside the directory where the command is executed.

    python r-pi/crosscompile.py setupcrosscompiler *setup location*
    python r-pi/crosscompile.py *setup location*

The *setupcompiler* line is required only if the cross-compilation environment hasn't been set up yet. If the environment has been set up, the line may be skipped.

When completed, *armory_<armory version>_raspbian-armhf.tar.gz* will be the final file. The user may be load it onto a Raspberry Pi (1 or 2 confirmed, 3 unconfirmed as of Mar. 2016), unzipped, and executed or installed as desired. *armory* is the command used to start Armory.

The initial environment setup will require upwards of 625MB worth of data to be downloaded. Please be patient.

## Caveats
Users will need to have *git*, *wget*, and the *dpkg* suite installed on their computers, on top of any materials required to compile Armory by itself. OS X users will also need the Xcode command line suite, as described in the OS X build instructions. If OS X users don't wish to compile *wget* and *dpkg* from source, the following *brew* command will work.

    brew install git wget dpkg

Despite the OS X instructions above, it is highly recommended for now that users not attempt to cross-compile on OS X. Tools required by the *PyQt* software suite may interfere with attempts to build Armory on OS X. For now, OS X users should install a Linux VM if they wish to cross-compile for an RPi.

As written, the script works but is a little primitive. Improvements are welcomed. One example is the fact that, when asked to set up the build environment, the script always attempts to download the required contents; it doesn't check to see if the environment already exists.
