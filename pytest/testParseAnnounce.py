import sys
sys.path.append('..')
from pytest.Tiab import TiabTest
import unittest

from armoryengine.parseAnnounce import *
from armoryengine.ArmoryUtils import *

changelogTestText = """
# This is a comment

       # Nothing to see here
#----------------------------------

Version 0.31
Released January 27, 2014

   - Major Feature 1
        This is a description of the first major feature.

   - Major Feature 2
        Description of 
        the second 
        big feature.  
 - Major Feature 3

        Indentations might be
    malformed


Version 0.30

   # No release date on this one
   - Major Feature 4
        Another multi-line 
        description

# I debated whetehr to put this next feature in there...
   # In the end I did
   - Major Feature 5
        Description of the fifth big feature.  

Version 0.25
Released April 21, 2013

   # I realize these feature numbers don't make sense for decreasing 
   # version numbers
   - Major Feature 6
        # Can we put comments
        This feature requires
        # in the middle of
        # the descriptions?
        interspersed comments

   - Major Feature 7

   - Major Feature 8
"""



fullFeatureLists = \
[ \
    [ '0.31', 'January 27, 2014',
        [ \
            ['Major Feature 1', 'This is a description of the first major feature.'], 
            ['Major Feature 2', 'Description of the second big feature.'], 
            ['Major Feature 3', 'Indentations might be malformed'] \
        ] \
    ], 
    [ '0.30', '',
        [ \
            ['Major Feature 4', 'Another multi-line description'], 
            ['Major Feature 5', 'Description of the fifth big feature.'] \
        ] \
    ], 
    [ '0.25', 'April 21, 2013',
        [ \
            ['Major Feature 6', 'This feature requires interspersed comments'], 
            ['Major Feature 7', ''], 
            ['Major Feature 8', ''] \
        ] \
    ] \
]
    


downloadTestText = """
-----BEGIN BITCOIN SIGNED MESSAGE-----

# Armory for Windows
Armory 0.91 Windows XP        32     http://url/armory_0.91_xp32.exe  3afb9881c32
Armory 0.91 Windows XP        64     http://url/armory_0.91_xp64.exe  8993ab127cf
Armory 0.91 Windows Vista,7,8 32,64  http://url/armory_0.91.exe       7f3b9964aa3


# Various Ubuntu/Debian versions
Armory 0.91 Ubuntu 10.04,10.10  32   http://url/armory_10.04-32.deb   01339a9469b59a15bedab3b90f0a9c90ff2ff712ffe1b8d767dd03673be8477f
Armory 0.91 Ubuntu 12.10,13.04  32   http://url/armory_12.04-32.deb   5541af39c84
Armory 0.91 Ubuntu 10.04,10.10  64   http://url/armory_10.04-64.deb   9af7613cab9
Armory 0.91 Ubuntu 13.10        64   http://url/armory_13.10-64.deb   013fccb961a

# Offline Bundles
ArmoryOffline 0.90 Ubuntu 10.04  32  http://url/offbundle-32-90.tar.gz 641382c93b9
ArmoryOffline 0.90 Ubuntu 12.10  32  http://url/offbundle-64-90.tar.gz 5541af39c84
ArmoryOffline 0.88 Ubuntu 10.04  32  http://url/offbundle-32-88.tar.gz 641382c93b9
ArmoryOffline 0.88 Ubuntu 12.10  32  http://url/offbundle-64-88.tar.gz 5541af39c84

# Windows 32-bit Satoshi (Bitcoin-Qt/bitcoind)
Satoshi 0.9.0 Windows XP,Vista,7,8 32,64 http://btc.org/win0.9.0.exe   837f6cb4981314b323350353e1ffed736badb1c8c0db083da4e5dfc0dd47cdf1
Satoshi 0.9.0 Ubuntu  10.04        32    http://btc.org/lin0.9.0.deb   2aa3f763c3b
Satoshi 0.9.0 Ubuntu  10.04        64    http://btc.org/lin0.9.0.deb   2aa3f763c3b

-----BEGIN BITCOIN SIGNATURE-----

HAZGhRr4U/utHgk9BZVOTqWcAodtHLuIq67TMSdThAiZwcfpdjnYZ6ZwmkUj0c3W
U0zy72vLLx9mpKJQdDmV7k0=
=i8i+
-----END BITCOIN SIGNATURE-----

"""




notifyTestText = """
-----BEGIN BITCOIN SIGNED MESSAGE-----
Comment: Signed by Bitcoin Armory v0.90.99

# PRIORITY VALUES:
#    Test announce:          1024
#    General Announcment:    2048
#    Important non-critical: 3072
#    Critical/security sens: 4096
#    Critical++:             5120

# 

UNIQUEID:   873fbc11
VERSION:    0
STARTTIME:  0
EXPIRES:    1500111222
CANCELID:   []
MINVERSION: 0.87.2
MAXVERSION: 0.88.1
PRIORITY:   4096
ALERTTYPE:  Security 
NOTIFYSEND: False
NOTIFYRECV: True
SHORTDESCR: Until further notice, require 30 confirmations for incoming transactions.
LONGDESCR:
   THIS IS A FAKE ALERT FOR TESTING PURPOSES:

   There is some turbulence on the network that may result in some transactions
   being accidentally reversed up to 30 confirmations.  A clever attacker may
   be able to exploit this to scam you.  For incoming transactions from
   parties with no existing trust, please wait at least 30 confirmations before
   considering the coins to be yours.

   By default, Armory will show you a checkmark when a transaction has 6
   confirmations.  You can hover your mouse over the checkmark in the ledger
   to display the actual number.  30 confirmations corresponds to approximately
   4-6 hours.
   *****


UNIQUEID:   113c948a
VERSION:    0
STARTTIME:  0
EXPIRES:    1700111222
CANCELID:   []
MINVERSION: *
MAXVERSION: <0.91.99.8
PRIORITY:   0
ALERTTYPE:  Upgrade
NOTIFYSEND: False
NOTIFYSEND: False
NOTIFYRECV: False
SHORTDESCR: New 0.92-beta testing version available.  Please download 0.91.99.8
LONGDESCR:
   The new version fixes the following bugs:
      - Bug A
      - Bug B
      - Bug C
*****
-----BEGIN BITCOIN SIGNATURE-----

HAZGhRr4U/utHgk9BZVOTqWcAodtHLuIq67TMSdThAiZwcfpdjnYZ6ZwmkUj0c3W
U0zy72vLLx9mpKJQdDmV7k0=
=i8i+
-----END BITCOIN SIGNATURE-----

"""




class parseChangelogTest(TiabTest):


   def setUp(self):
      self.clh = changelogParser(changelogTestText)
      
   def tearDown(self):
      pass


   # TODO: This test needs more verification of the results.
   def testReadAll(self):
      
      expectedOutput = fullFeatureLists[:]
      testOutput = self.clh.getChangelog()

      for test,expect in zip(testOutput, expectedOutput):
         self.assertEqual( test[0], expect[0] )
         
         for testFeat, expectFeat in zip(test[1], expect[1]):
            self.assertEqual( testFeat, expectFeat )


   def testStopAt028(self):

      expectedOutput = fullFeatureLists[:]
      testOutput = self.clh.getChangelog(getVersionInt([0,28,0,0]))

      for test,expect in zip(testOutput, expectedOutput):
         self.assertEqual( test[0], expect[0] )
         
         for testFeat, expectFeat in zip(test[1], expect[1]):
            self.assertEqual( testFeat, expectFeat )


################################################################################
class parseDownloadTest(TiabTest):
   
   def setUp(self):
      self.dl = downloadLinkParser(filetext=downloadTestText)

   def tearDown(self):
      pass


   def testParseDL(self):

      dllink = self.dl.getDownloadLink('Armory','0.91','Windows','XP','32')
      self.assertEqual(dllink, ['http://url/armory_0.91_xp32.exe', '3afb9881c32'])

      dllink = self.dl.getDownloadLink('Armory','0.91','Windows','Vista','32')
      self.assertEqual(dllink, ['http://url/armory_0.91.exe', '7f3b9964aa3'])

      # This is a real file with a real hash, for testing DL in Armory
      dllink = self.dl.getDownloadLink('Satoshi','0.9.0','Windows','7','64')
      self.assertEqual(dllink, ['http://btc.org/win0.9.0.exe',
            '837f6cb4981314b323350353e1ffed736badb1c8c0db083da4e5dfc0dd47cdf1'])

      dllink = self.dl.getDownloadLink('ArmoryOffline','0.88','Ubuntu','10.04','32')
      self.assertEqual(dllink, ['http://url/offbundle-32-88.tar.gz', '641382c93b9'])

      dllink = self.dl.getDownloadLink('Armory','1.01','WIndows','10.04','32')
      self.assertEqual(dllink, None)



################################################################################
class parseNotifyTest(TiabTest):
   
   def setUp(self):
      self.notify = notificationParser(filetext=notifyTestText)

   def tearDown(self):
      pass

   def testParseNotify(self):

      notifyMap = self.notify.getNotificationMap()


      self.assertEqual(notifyMap['873fbc11']['VERSION'], '0')
      self.assertEqual(notifyMap['873fbc11']['CANCELID'], '[]')
      self.assertEqual(notifyMap['873fbc11']['MAXVERSION'], '0.88.1')
      self.assertTrue(notifyMap['873fbc11']['LONGDESCR'].strip().startswith('THIS IS A FAKE'))

      self.assertEqual(notifyMap['113c948a']['VERSION'], '0')
      self.assertEqual(notifyMap['113c948a']['CANCELID'], '[]')
      # This is a bogus assertion that must fail unless updated on every release:
      # self.assertEqual(notifyMap['113c948a']['MAXVERSION'], '0.91.99.7')
      self.assertTrue(notifyMap['113c948a']['LONGDESCR'].strip().startswith('The new version'))

# Running tests with "python <module name>" will NOT work for any Armory tests
# You must run tests with "python -m unittest <module name>" or run all tests with "python -m unittest discover"
# if __name__ == "__main__":
#    unittest.main()

