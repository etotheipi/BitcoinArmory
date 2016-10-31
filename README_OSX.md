# macOS (OS X) README
## Requirements
Armory will run on OS X 10.7 and beyond. However, due to code changes that aren't supported under 10.7, it is highly recommended that users, if possible, upgrade to OS X 10.8 or higher. Armory will run on 10.7 for now. However, *Armory developers may not fix bugs found under 10.7*. Users who are completely unable to upgrade beyond 10.7 should make mitigation plans; Armory will eventually require OS X 10.8.

Due to [Twisted](http://twistedmatrix.com/trac/) and [Python](https://python.org/) requirements that can't be met by macOS 10.12 (Sierra), users must use `brew` to install an updated version of OpenSSL in order for Armory 0.95.1 to run. Please follow these instructions.

1. Open a terminal and run the `brew` command. If `brew` is not found, please execute the following commands from the command line. If the final command returns any errors, consult Google, the *bitcoin-armory* IRC channel on Freenode, or the [Bitcoin Forum](https://bitcointalk.org/index.php?board=97.0) for further instructions.

        /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
        touch ~/.bashrc
        echo "export CFLAGS=\"-arch x86_64\"" >> ~/.bashrc
        echo "export ARCHFLAGS=\"-arch x86_64\"" >> ~/.bashrc
        source ~/.bashrc
        brew update
        brew doctor

2. If everything is successful, execute the following command.

        brew install openssl

You may now run Armory.

## macOS-specific Bugs
Armory developers make a best effort to ensure that all Armory features are available on all versions of Armory. Unfortunately, there are rare cases where the OS X version is missing features or has bugs not found elsewhere. The following is a list of known bugs/issues. Please report any other bugs on the [Bitcoin Forum](https://bitcointalk.org/index.php?board=97.0) or on the *bitcoin-armory* IRC channel on Freenode.

- Due to unknown issues with multithreading on Qt 4 (a library Armory uses), there are rare instances where Armory may crash suddenly. The Armory team has done its best to mitigate the crashes, with very few users reporting any crashes at all. Armory developers themselves haven't experienced any such crashes since approximately June 2015.
- The "File Open" dialog under OS X Armory is very "dumb." (This is due to an unknown Qt 4 bug that causes Armory to crash whenever a much nicer dialog is opened.) Opening files in certain locations (e.g., thumb drives) is very difficult. The only consistent solutions are to copy files over to a location that can be opened, or to generate a [symbolic link](http://askubuntu.com/questions/600714/creating-a-symlink-from-one-folder-to-another-with-different-names) to the desired directory.
