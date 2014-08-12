import sys
sys.path.append('..')
from pytest.Tiab import TiabTest
from armoryengine.ALL import *
from announcefetch import AnnounceDataFetcher
import unittest


forceTestURL = 'https://s3.amazonaws.com/bitcoinarmory-testing/testannounce.txt'
fetchDump = './fetchedFiles'

class AnnouncementTester(TiabTest):

   def setUp(self):
      pass

   def tearDown(self):
      pass

   def testNoStart(self):
      adf = AnnounceDataFetcher(forceTestURL, fetchDir=fetchDump)
      adf.setFetchInterval(20)

      self.assertFalse(adf.isDisabled())
      self.assertFalse(adf.atLeastOneSuccess())

   def testStart(self):
      adf = AnnounceDataFetcher(forceTestURL, fetchDir=fetchDump)
      adf.setFetchInterval(20)

      print 'STARTING',
      print '   Running:', adf.isRunning(), 
      print '   OneSuccess:', adf.atLeastOneSuccess(), 
      print '   #Files',adf.numFiles()

      print 'Attempting to fetch before ADF is started'
      d = adf.getAnnounceFile('notify')
      print '*****'
      print 'LENGTH OF NOTIFY FILE:', (len(d) if d else 0)
      print '*****'
      print 'Attempting to fetch before ADF is started (forced)'
      d = adf.getAnnounceFile('notify', forceCheck=True)
      print '*****'
      print 'LENGTH OF NOTIFY FILE:', (len(d) if d else 0)
      print '*****'
      adf.start()
   
      t = 0
      try:
         while True:
            time.sleep(0.5)
            t += 0.5

            print '   Running:', adf.isRunning(), 
            print '   OneSuccess:', adf.atLeastOneSuccess(), 
            print '   #Files',adf.numFiles()

            if 10<t<11 or 14<t<15:
               s = RightNow()
               d = adf.getAnnounceFile('notify') 
               print '*****'
               print 'LENGTH OF NOTIFY FILE:', (len(d) if d else 0)
               print '*****'
               print 'took %0.6f seconds' % (RightNow() - s)

            if 30<t<31 or 34<t<35:
               s = RightNow()
               d = adf.getAnnounceFile('notify', forceCheck=True) 
               print '*****'
               print 'LENGTH OF NOTIFY FILE:', (len(d) if d else 0)
               print '*****'
               print 'took %0.6f seconds' % (RightNow() - s)

            if t>40:
               adf.shutdown()

            if not adf.isRunning():
               print 'Attempting to fetch after shutdown'
               d = adf.getAnnounceFile('notify')
               print '*****'
               print 'LENGTH OF NOTIFY FILE:', (len(d) if d else 0)
               print '*****'
               print 'Attempting to fetch after shutdown (forced)'
               d = adf.getAnnounceFile('notify', forceCheck=True)
               print '*****'
               print 'LENGTH OF NOTIFY FILE:', (len(d) if d else 0)
               print '*****'
               break

      except KeyboardInterrupt:
         print 'Exiting...'


# Running tests with "python <module name>" will NOT work for any Armory tests
# You must run tests with "python -m unittest <module name>" or run all tests with "python -m unittest discover"
# if __name__ == "__main__":
#    unittest.main()
