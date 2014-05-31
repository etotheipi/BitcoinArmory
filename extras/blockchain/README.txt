Forum thread on BitcoinTalk:
https://bitcointalk.org/index.php?topic=145386.0

Bitcoin-Qt/bitcoind version 0.7.1 and later supports a special import feature:  If the file "bootstrap.dat" is found in the bitcoin data directory, it will validate and import all blockchain data found in that file.  The following torrent presents a bootstrap.dat file for that feature.

----------------------
What is bootstrap.dat?

It is a flat, binary file containing bitcoin blockchain data, from the genesis block through a recent height.

Versions 0.7.1+ automatically validates and imports a file in the data directory named "bootstrap.dat".

Special note: Version prior to 0.8.0 have a bug which will only import 2G of data from a file.  This is fixed in 0.8.0.

------------------------
Who wants bootstrap.dat?

Anyone bringing up a new node using the reference client.  This is one method of accelerating the initial blockchain download process, while helping the bitcoin P2P network by offloading data download traffic from public P2P nodes.

This download is not for those who are already running the bitcoin client.

---------------------------------------
How often will this torrent be updated?

Assuming this project is deemed useful and worth continuing... the torrent will be updated once every few months, when the checkpoints are updated in the reference client source code.

--------------------------------------
Why not update the torrent more often?

A torrent works best when it is a large, static dataset that changes infrequently.  That maximizes the ability to seed the data, enabling even part-timer seeders to contribute meaningfully.  Less frequent changes also minimizes the risk that a malicious torrent will appear, with a long, malicious side chain.  The current policy only updates the torrent after blocks are buried many thousands deep in the chain.

-----------------------
Why should I trust you?

You don't have to:  This data is raw block chain data.  The client will verify this data during import.

Independent third parties may generate their own bootstrap.dat, up to a recent height, and verify that the sha256sum matches that posted above.  The file format is simple and publicly known:

     <4-byte pchMessageStart><32-bit length><CBlock, serialized in network wire format>

----------------------------------------
How can I help?  Do you need more seeds?

Yes, we need as many long term seeds as possible.  This ensures we can meet torrent download demand immediately at high speeds, and remain idle the remainder of the time.
