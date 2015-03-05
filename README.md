##Armory

**Created by Alan Reiner on 13 July, 2011**

[Armory](https://github.com/etotheipi/BitcoinArmory) is a full-featured Bitcoin client, offering a dozen innovative features not found in any other client software! Manage multiple wallets (deterministic and watching-only), print paper backups that work forever, import or sweep private keys, and keep your savings in a computer that never touches the internet, while still being able to manage incoming payments, and create outgoing payments with the help of a USB key.

Multi-signature transactions are accommodated under-the-hood about 80%, and will be completed and integrated into the UI soon.

**Armory has no independent networking components built in.** Instead, it relies on on the Satoshi client to securely connect to peers, validate blockchain data, and broadcast transactions for us.  Although it was initially planned to cut the umbilical cord to the Satoshi client and implement independent networking, it has turned out to be an inconvenience worth having. Reimplementing all the networking code would be fraught with bugs, security holes, and possible blockchain forking.  The reliance on Bitcoin-Qt right now is actually making Armory more secure!

##Donations

Please take a moment to donate! 1ArmoryXcfq7TnCSuZa9fQjRYwJ4bkRKfv

![bitcoin:1ArmoryXcfq7TnCSuZa9fQjRYwJ4bkRKfv][Donation Image]

##Building Armory From Source

See instructions [here][Armory Build Instructions]


##Dependencies

* GNU Compiler Collection  
 Linux:   Install package `g++`

* Crypto++  
 Linux:   Install package `libcrypto++-dev`  
 Windows: [Download][Windows Crypto Download]    
  
* SWIG  
 Linux:   Install package `swig`  
 Windows: [Download][Windows SWIG Download]  
 MSVS: Copy swigwin-2.x directory next to cryptopp as `swigwin`  
  
* Python 3.4
 Linux:   Install package `python3-dev` and `python3-pip`
 Windows: [Download][Windows Python Download]  
  
* Python Packages
 Linux:   Install python packages `pip3 install twisted psutil`
 Windows: [Download Twisted][Windows Twisted Download]  [Download psutil][Windows psutil Download
  
* Qt 5
 Linux:   Install packages `libqt5designer5 libqt5gui5 libqt5help5 libqt5printsupport5 libqt5widgets5 python3-pyqt5 pyqt5-dev-tools`
 Windows: [Download QT][Windows QT Download] [Download SIP][Windows SIP Download] [Download PyQT5][Windows PyQt Download]


##Sample Code

Armory contains over 25,000 lines of code, between the C++ and python libraries.  This can be very confusing for someone unfamiliar with the code (you).  Below I have attempted to illustrate the CONOPS (concept of operations) that the library was designed for, so you know how to use it in your own development activities.  There is a TON of sample code in the following:

* C++ -   [BlockUtilsTest.cpp](cppForSwig/BlockUtilsTest.cpp)
* Python -   [Unit Tests](pytest/), [sample_armory_code.py](extras/sample_armory_code.py)


##License

Distributed under the GNU Affero General Public License (AGPL v3)  
See [LICENSE file](LICENSE) or [here][License]

##Copyright

Copyright (C) 2011-2015, Armory Technologies, Inc.


[Armory Build Instructions]: https://bitcoinarmory.com/building-from-source
[Windows Crypto Download]: http://www.cryptopp.com/#download
[Windows SWIG Download]: http://www.swig.org/download.html
[Windows Python Download]: http://www.python.org/getit/
[Windows Twisted Download]: http://twistedmatrix.com/trac/wiki/Downloads
[Windows QT Download]: http://www.qt.io/download-open-source/#section-5
[Linux QT Download]: http://www.qt.io/download-open-source/#section-3
[QT4 Reactor Download]: https://launchpad.net/qt4reactor
[Windows PyWin Download]: http://sourceforge.net/projects/pywin32/files/pywin32/
[Windows Py2Exe Download]:  http://www.py2exe.org/
[License]: http://www.gnu.org/licenses/agpl.html
[Donation Image]: https://chart.googleapis.com/chart?chs=250x250&cht=qr&chl=bitcoin:1ArmoryXcfq7TnCSuZa9fQjRYwJ4bkRKfv?&label=Armory+Donation
[Linux PyQt Download]: http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.4.1/PyQt-gpl-5.4.1.tar.gz
[Windows PyQt Download]: http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.4.1/PyQt-gpl-5.4.1.zip
[Linux SIP Download]: http://sourceforge.net/projects/pyqt/files/sip/sip-4.16.6/sip-4.16.6.tar.gz
[Windows SIP Download]: http://sourceforge.net/projects/pyqt/files/sip/sip-4.16.6/sip-4.16.6.zip
[Windows psutil Download]: https://pypi.python.org/pypi/psutil/