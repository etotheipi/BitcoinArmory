**Copyright (C) 2011-2015, Armory Technologies, Inc.**

**Distributed under the GNU Affero General Public License (AGPL v3)**

**See LICENSE or http://www.gnu.org/licenses/agpl.html**

Description
-----------

Webshop is a simple web store that works with bitcoin and armoryd. This is meant to be a demonstration of the ways armoryd can be leveraged to take payments in bitcoin.

Dependencies
------------
 
   * Flask - Install package "python-flask"
   * SocketIO - Use pip to install "flask-socketio"

How to run
----------

1. Create a wallet using ArmoryQt.

2. Start armoryd in testnet:

  `python armoryd.py --testnet`

3. Start the webshop server:

  `cd webshop`

  `python server.py`

4. Go to the url:

  `http://localhost:5000`
