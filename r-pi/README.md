# RASPBERRY PI CROSS-COMPILATION INSTRUCTIONS

I don't know that the original instructions and associated python script still work, since the project build process was redone with autotools.

Here are the instructions to cross compile Armory for RPi manually (valid since 0.96):

1) Get a RPi cross compiler. You can either build one yourself or get the pre built ones from RPi repo:

https://github.com/raspberrypi/tools

2) Make sure the xcompiler /bin is added to your PATH. As an example, if you cloned the RPi tools repo in $HOME/RPi, you'd add the following to your PATH:

PATH="$PATH:$HOME/RPi/tools/arm-bcm2708/gcc-linaro-arm-linux-gnueabihf-raspbian-x64/bin"

3) Grab the libpython2.7-dev package for armhf. This holds the pyconfig.h the SWIG'd interface needs to build. 

Extract the package, you should end up with /usr folder. To follow up on the example, we will extract the packagae to ~/RPi.

4) configure Armory for xcompiling to the target arch (here we follow on the previous example and use the compiler suite added to PATH):

	sh autogen.sh
	./configure --host=arm-linux-gnueabihf

5) Finally, in order to build, you need to tell make where to look for that extra python include folder. The makefile has a special variable set for this purpose: EXTRA_PYTHON_INCLUDES

To complete the example, this is how you'd call make:

	make -j8 EXTRA_PYTHON_INCLUDES=-I~/RPi/usr/include

Do not forget the leading -I. You should also avoid using ~/, give it the full path instead.




#########################Old instructions#####################################
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
