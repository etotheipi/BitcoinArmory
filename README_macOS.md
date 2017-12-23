# macOS README
## Requirements
Armory will run on macOS 10.8 and beyond. It is highly recommended to install Armory on the newest version of macOS that is feasible, as Apple often introduces changes to newer versions that make support of older versions difficult, if not impossible.

Due to [Python](https://python.org/) requirements that can't be met by default on macOS, users must use `brew` to install an updated version of OpenSSL in order for Armory to run. Please follow these instructions.

1. Open a terminal and run the `brew` command. If `brew` isn't found, please execute the following commands from the terminal (aka command line). If the final command returns any errors, consult Google, the *bitcoin-armory* IRC channel on Freenode, or the [Bitcoin Forum](https://bitcointalk.org/index.php?board=97.0) for further instructions.

        /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
        touch ~/.bashrc
        echo "export CFLAGS=\"-arch x86_64\"" >> ~/.bashrc
        echo "export ARCHFLAGS=\"-arch x86_64\"" >> ~/.bashrc
        source ~/.bashrc
        brew update
        brew doctor

2. If everything is successful, execute the following command.

        brew install openssl

## Downloading and Verifying Armory
Official Armory builds are signed by goatpig, the lead maintainer. However, goatpig isn't a member of the [Apple Developer Program](https://developer.apple.com/). Therefore, he can't sign Armory with an official key from Apple. Due to [Gatekeeper](https://support.apple.com/en-us/HT202491) requirements, this can prevent Armory from being run immediately upon unzipping files posted by goatpig. There are two possible solutions, but first, it is highly recommended that users verify builds posted by goatpig. The following steps will verify the code, and are adopted from [the official verification directions for Linux](https://btcarmory.com/docs/verify). For the sake of this example, assume the version of Armory is 2.4.1.99.

1. Install [GPG Suite](https://gpgtools.org/) if it hasn't been installed already. (If you can run `gpg` on the terminal or see GPG Keychain in the Launchpad, GPG Suite has been installed.)

2. Open the terminal.

3. **PERFORM THIS STEP ONLY ONCE FOR YOUR MACHINE.** Download and import the [official signing key](https://keyserver.ubuntu.com/pks/lookup?search=goatpig) (GPG fingerprint 4922589A as of Nov. 2017). Make sure the fingerprint matches the fingerprint on the key server!

        gpg --recv-keys --keyserver keyserver.ubuntu.com 4922589A

4. Download the appropriate macOS build [from the release page](https://github.com/goatpig/BitcoinArmory/releases/) (e.g., *armory\_2.4.1.99\_osx.tar.gz*), along with *sha256sum.txt.asc*, which will contain a GPG-signed list of SHA-256 hashes of the code posted by goatpig. If a macOS-specific *shasum* file is unavailable, try *sha256sum.txt.asc* instead.

5. Verify the SHA-256 hash of the macOS build.

        shasum -a 256 -c sha256sum.txt.asc armory_2.4.1.99_osx.tar.gz 2>&1 | grep OK

   If you see `armory_2.4.1.99_osx.tar.gz: OK` in the terminal, the code is an exact copy of what goatpig posted.

6. Verify that the SHA-256 hash list was actually signed by goatpig.

        gpg --verify sha256sum.txt.asc

   If you see `gpg: Good signature from "goatpig (Offline signing key for Armory releases) <moothecowlord@gmail.com>" [unknown]` in the terminal, the SHA-256 hash list was signed by goatpig. If the macOS code has the correct hash and the list of hashes were signed by goatpig, you now know the code is exactly what was uploaded by goatpig.

If verification fails at any point, double-check the commands you're running, and double check the fingerprint on the Ubuntu keyserver. If the fingerprints match and the commands are correct, [please post on Bitcoin Forum's Armory subforum](https://bitcointalk.org/index.php?board=97.0) or the *bitcoin-armory* IRC channel on Freenode and notify goatpig immediately.

## Running Armory
Once the builds are verified, the following steps should be followed. (Note that these steps aren't required by people who compile their own version of Armory.)

1. Upon unzipping Armory, move Armory to a new directory. Moving Amrory into /Applications will make Armory accessible from the Launchpad.

2. Follow [these directions from Apple](https://support.apple.com/kb/PH25088?locale=en_US) to ensure that Armory will run successfully.

3. The first time a new version of Armory is run, macOS will ask if you wish to run the program. Click "Yes" and continue on. If macOS is stubborn and won't run Armory, you'll have to go to "Security & Privacy" under "System Preferences". From there, under "General", you should see a note about "Armory.app" not being able to run. Depending on which version of macOS you have, you have two options, both of which apply to the "Allow apps downloaded from" setting.

   3.1. On macOS versions starting with 10.13, you'll see the message "'Armory.app' was blocked from opening because it isn't from an identified developer." Click "Open Anyway" and continue on, ignoring the aforementioned warning about unsigned code. Be sure that you are selecting the option *only* for Armory, and not for other programs!

   3.2. If the option in Step 2.1 is unavailable, there is an alternative. On all supported versions of macOS, click the lock and unlock it, choose "Anywhere", re-lock the system, and start Armory, ignoring the unsigned code warning. (If the "Anywhere" option isn't seen, [follow these instructions](http://osxdaily.com/2016/09/27/allow-apps-from-anywhere-macos-gatekeeper/) to bring it up.) If you wish, you may reset the "Allow apps downloaded from" setting to a more strict setting at this point. macOS will remember that you allowed Armory to run.

## Compiling Armory
See the [macOS build README](osxbuild/OSX_build_notes.md) for more info.

## Running armoryd
As of 2017, armoryd (a JSON-RPC daemon for Armory) is [in its own repo](https://github.com/goatpig/armoryd), separate from Armory. If users wish to run armoryd under macOS, the easiest solution is to open up Armory.app and place armoryd.py alongside the Armory codebase (Contents/MacOS/py/usr/local/lib/armory). The user can then execute the script that kicks off armoryd (`Contents/MacOS/armoryd`).

## macOS-specific Bugs
Armory developers make a best effort to ensure that all Armory features are available on all versions of Armory. Unfortunately, there are rare cases where the macOS version is missing features or has bugs not found elsewhere. The following is a list of known bugs/issues. Please report any other bugs on the [Bitcoin Forum](https://bitcointalk.org/index.php?board=97.0) or on the *bitcoin-armory* IRC channel on Freenode.

- Due to unknown issues with multithreading on Qt 4 (a library Armory uses), there are rare instances where Armory may crash suddenly. The Armory team has done its best to mitigate the crashes, with very few users reporting any crashes at all. Armory developers themselves haven't experienced any such crashes since approximately June 2015, and no users have reported such issues since around that time.
- The "File Open" dialog under macOS Armory is very "dumb." This is due to an unknown Qt 4 bug that causes Armory to crash whenever a "native" dialog is opened. This means opening files in certain locations (e.g., thumb drives) is very difficult. The only consistent solutions are to copy files over to a location that can be opened, or to generate a [symbolic link](http://askubuntu.com/questions/600714/creating-a-symlink-from-one-folder-to-another-with-different-names) to the desired directory.
