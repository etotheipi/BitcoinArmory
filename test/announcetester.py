
import os
import sys
import time
import unittest

sys.path.append('..')

from armoryengine.ALL import *
from announcefetch import AnnounceDataFetcher


forceTestURL = 'https://s3.amazonaws.com/bitcoinarmory-testing/testannounce.txt'
fetchDump = './fetchedFiles'

class AnnouncementTester(unittest.TestCase):

   def setUp(self):
      pass

   def tearDown(self):
      pass

   def testNoStart(self):
      adf = AnnounceDataFetcher(forceTestURL, fetchDump)
      adf.setFetchInterval(20)

      self.assertFalse(adf.isDisabled())
      self.assertFalse(adf.atLeastOneSuccess())

   def testStart(self):
      adf = AnnounceDataFetcher(forceTestURL, fetchDump)
      adf.setFetchInterval(20)

      print 'Started: ', adf.isRunning(), adf.atLeastOneSuccess(), adf.numFiles()
      adf.start()
   
      t = 0
      try:
         while True:
            time.sleep(0.5)
            t += 0.5
            print 'Running: ', adf.isRunning(), adf.atLeastOneSuccess(), adf.numFiles()

            if 10<t<11 or 14<t<15:
               s = RightNow()
               d = adf.getFetchedFile('notify') 
               print '*****'
               print d
               print '*****'
               print 'took %0.6f seconds' % (RightNow() - s)

            if 30<t<31 or 34<t<35:
               s = RightNow()
               d = adf.getFetchedFile('notify', forceFetch=True) 
               print '*****'
               print d
               print '*****'
               print 'took %0.6f seconds' % (RightNow() - s)

      except KeyboardInterrupt:
         print 'Exiting...'


if __name__ == "__main__":
   del sys.argv[1:]
   unittest.main()
