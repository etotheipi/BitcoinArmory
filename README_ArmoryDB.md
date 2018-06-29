# ArmoryDB
ArmoryDB is a binary used by Armory. The code is written in C++11 and is used to control the [LMDB](http://symas.com/mdb/) databases used by Armory. These databases contain information about the wallets/lockboxes in Armory and information about transactions relevant to the wallets.

ArmoryDB is automatically called whenever Armory starts up; the user needs not intervene. Only advanced users who know what they're doing need any further.

## ArmoryDB usage
ArmoryDB works by reading the blockchain downloaded by Bitcoin Core and finding any transactions relevant to the wallets loaded into Armory. This means that the entire blockchain must be rescanned whenever a new wallet or lockbox is loaded. Once a wallet/lockbox has been loaded and the blockchain fully scanned for that wallet, ArmoryDB will keep an eye on the blockchain. Any transactions relevant to the addresses controlled by wallets/lockboxes will be resolved. In addition, as Armory builds its own mempool by talking to the Core node, any relevant zero-confirmation transactions will be resolved by ArmoryDB.

As of v0.96.4, Armory calls ArmoryDB using a particular set of flags. The Armory Python log (`armorylog.txt`) shows attempts at executing ArmoryDB using some default parameters, assuming that `/home/snakamoto` is the user's root directory.

```
2018-01-13 13:32:17 (WARNING) -- SDM.py:396 - Spawning DB with command: /home/snakamoto/Armory/ArmoryDB --db-type="DB_FULL" --cookie --satoshi-datadir="/home/snakamoto/.bitcoin/blocks" --datadir="/home/snakamoto/Armory/" --dbdir="/home/snakamoto/Armory/databases"
2018-01-13 13:32:17 (INFO) -- ArmoryUtils.py:679 - Executing popen: ['/home/snakamoto/Armory/ArmoryDB', '--db-type="DB_FULL"', '--cookie', '--satoshi-datadir="/home/snakamoto/.bitcoin/blocks"', '--datadir="/home/snakamoto/Armory/"', '--dbdir="/home/snakamoto/Armory/databases"']
```

The flags are explained below, as seen in the Armory source code. By default, like Armory, ArmoryDB works on the mainnet network.

* cookie: Create a cookie file holding a random authentication key to allow local clients to make use of elevated commands (e.g., `shutdown`). (Default: False)
* datadir: Path to the Armory data folder. (Default: Same as Armory)
* db-type: Sets the db type. Database type cannot be changed in between Armory runs. Once a database has been built with a certain type, the database will always function according to the initial type; specifying another type will do nothing. Changing the database type requires rebuilding the database. (Default: DB\_FULL)
* dbdir: Path to folder containing the Armory database file directory. If empty, a new database will be created. (Default: Same as Armory)
* satoshi-datadir: Path to blockchain data folder (blkXXXXX.dat files). (Default: Same as Armory)

The database types are as follows:

* DB\_BARE: Tracks wallet history only. Smallest DB, as the DB doesn't resolve a wallet's relevant transaction hashes until requested. (In other words, database accesses will be relatively slow.) This was the default database type in Armory v0.94.
* DB\_FULL: Tracks wallet history and resolves all relevant transaction hashes. (In other words, the database can instantly pull up relevant transaction data). ~1GB minimum size for the database. Default database type as of v0.95.
* DB\_SUPER: Tracks the entire blockchain history. Any transaction hash can be instantly resolved into its relevant data. Not fully implemented yet, and the database will be at least ~100GB large.

There are additional flags.

* checkchain: A test mode of sorts. It checks all the signatures in the blockchain. (Default: False)
* clear\_mempool: Delete all zero confirmation transactions from the database. (Default: False)
* fcgi-port: Sets the database listening port. The database listens to external connections (e.g., from Armory) via FCGI and can be placed behind an HTTP daemon in order to obtain remote access to ArmoryDB. (Default: 9001 (mainnet) / 19001 (testnet) / 19002 (regtest))
* listen-all: Listen to all incoming IPs (not just localhost). (Default: False)
* ram-usage: Defines the RAM use during database scan operations. One point averages 128MB of RAM (without accounting for the base amount, ~400MB). Can't be lower than one point. Can be changed in between Armory runs. (Default: 50)
* rebuild: Delete all DB data, and build the database and scan the blockchain data from scratch.
* regtest: Run database against the regression test network.
* rescan: Delete all processed history data and rescan blockchain from the first block.
* rescanSSH: Delete balance and transaction count data, and rescan the data. Much faster than rescan or rebuild.
* satoshirpc-port: Set the P2P port of the Core node to which ArmoryDB will attempt to connect. (Default: Same as Armory)
* testnet: Run database against the testnet network.
* thread-count: Defines how many processing threads can be used during database builds and scans. Can't be lower than one thread. Can be changed in between Armory runs. (Default: The maximum number of available CPU threads.)
* zcthread-count: Defines the maximum number on threads the zero-confirmation (ZC) parser can create for processing incoming transcations from the Core network node. (Default: 100)

Note that the flags may be added to the Armory root data directory in an ArmoryDB config file (`armorydb.conf`). The file will set the parameters every time ArmoryDB is started. Command line flags, including flags used by Armory, will override config values. (Changing Armory's default values will require recompilation.) An example file that mirrors the default parameters used by Armory can be seen below. Yeah!

```
db-type="DB_FULL"
cookie=1
satoshi-datadir="/home/snakamoto/.bitcoin/blocks""
datadir="/home/snakamoto/Armory/"
dbdir="/home/snakamoto/Armory/databases"
```

As always, check the source code for the most up-to-date information.

## ArmoryDB connection design
ArmoryDB *must* run alongside the Bitcoin Core node. This is because ArmoryDB does a memory map on the blockchain files. This can only be done if ArmoryDB and the node are running on the same OS and, ideally, on the same storage device. The IP address of the Core node is hardcoded (localhost) and can't be changed without recompiling Armory (and changing the design at your own risk!). Only the node's port can be changed via the `satoshirpc-port` parameter. This design may be changed in the future.

It is possible for Armory and other clients to talk to ArmoryDB remotely. Possibilities for reaching ArmoryDB include placing ArmoryDB behind an HTTP daemon or logging into the ArmoryDB machine remotely via VPN. Talking to ArmoryDB is done via JSON-encoded packets, as seen in the `armoryd` project.

## Dependencies
* fcgi - Communication protocol - [Source of goatpig's libfcgi fork](https://github.com/toshic/libfcgi)
* Clang (macOS) - Installed automatically by [Xcode](https://developer.apple.com/xcode/)
* GNU Compiler Collection (Linux) - Install package `g++`
* LMDB - Database engine, modified to suit Armory's use cases - [LMDB page](http://symas.com/mdb/)
* Visual Studio compiler (Windows) - [Visual Studio page](https://www.visualstudio.com/)

## Troubleshooting
Occasionally, a user may have trouble connecting to the Bitcoin Core node. Often, this is because a version of ArmoryDB from a previous run of Armory didn't shut down properly. If a user is unable to connect to the Core node, the following steps are recommended.

* Shut down Armory.
* Check the operating system's task manager 30-60 seconds later.
* If ArmoryDB is still running, shut it down manually.
* Restart Armory.

## License
Distributed under the MIT License. See the [LICENSE file](LICENSE) for more information.

## Copyright
Copyright (C) 2017-2018 goatpig
