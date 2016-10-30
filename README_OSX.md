# macOS (OS X) README
## Requirements
As of Armory 0.95.1, due to Python requirements that can't be met by macOS 10.12 (Sierra), users must use `brew` to install an updated version of OpenSSL in order for Armory to run. Please follow these instructions.

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
- If any bugs are found, report them on the *bitcoin-armory* IRC channel on Freenode, or the [Bitcoin Forum](https://bitcointalk.org/index.php?board=97.0).
- Due to unknown issues with multithreading on Qt 4 (a library Armory uses), there are rare instances where Armory may crash suddenly. The Armory team has done its best to mitigate the crashes, with some users not reporting any crashes at all.
