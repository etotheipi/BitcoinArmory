'''
Created on Aug 30, 2013

@author: Andy
'''
import sys
sys.argv.append('--nologging')
from sys import argv, path
import os

from armoryengine import PyBtcWallet
from utilities.ArmoryUtils import RightNow
from CppBlockUtils import SecureBinaryData
from operator import add, mul
# Give an upper limit for any method to return
# if the limit is exceded raise MaxResultsExceeded exception
MAX_LIST_LEN = 20000000

class MaxResultsExceeded(Exception): pass

path.append('..')
path.append('/usr/bin/armory')

def loadWallet():
   if len(argv)<2:
      print '***USAGE: '
      print '    %s /path/to/wallet/file.wallet' % argv[0]
      exit(0)
   walletPath = argv[1]
   if not os.path.exists(walletPath):
      print 'Wallet does not exist:'
      print '  ', walletPath
      exit(0)
   return PyBtcWallet().readWalletFile(walletPath)


def printMaxResultsExceededAndExit():
   print "To many passwords to try. Please reduce the scope of your search."
   exit(1)

class PwdSeg(object):
   def __init__(self, known):
      self.known = known
   
   # Abstract method
   def getSegList(self, maxResults=MAX_LIST_LEN):
      raise NotImplementedError("Subclass must implement getSegList()")
   
   # Abstract method
   def getSegListLen(self):
      raise NotImplementedError("Subclass must implement getSegListLength()")

class UnknownCaseSeg(PwdSeg):
   def __init__(self, known):
      super(UnknownCaseSeg, self).__init__(known)
   
   getBothCases = lambda self, ch : [ch.lower(), ch.upper()] if ch.lower() != ch.upper() else [ch]
   
   getSegListRecursion = lambda self, seg : \
      [a + b \
         for a in self.getBothCases(seg[0]) \
         for b in self.getSegListRecursion(seg[1:])] if len(seg)>0 else ['']
   
   def getSegListLen(self):
      return reduce(mul, [1 if ch.lower() == ch.upper() else 2 for ch in self.known]) 
   
   def getSegList(self, maxResults=MAX_LIST_LEN):
      if self.getSegListLen() > maxResults:
         raise MaxResultsExceeded
      return self.getSegListRecursion(self.known)
   
class KnownSeg(PwdSeg):
   def __init__(self, known):
      super(KnownSeg, self).__init__(known)
   
   def getSegListLen(self):
      return 1
   
   def getSegList(self, maxResults=MAX_LIST_LEN):
      return [self.known]

class UnknownSeg(PwdSeg):
   def __init__(self, known, minLen, maxLen):
      super(UnknownSeg, self).__init__(known)
      self.removeDups()
      self.minLen = minLen
      self.maxLen = maxLen
      
   def removeDups(self):
      self.known = ''.join(set(self.known))
      
   getSegListRecursion = lambda self, segLen : \
      [a + b \
         for a in self.known \
         for b in self.getSegListRecursion(segLen-1)] if segLen > 0 else ['']
   
   def getSegListLen(self):
      return reduce(add, [len(self.known) ** i for i in range(self.minLen, self.maxLen + 1)]) 
   
   def getSegList(self, maxResults=MAX_LIST_LEN):
      if self.getSegListLen() > maxResults:
         raise MaxResultsExceeded
      return reduce(lambda x,y : x + self.getSegListRecursion(y),
                    range(self.minLen, self.maxLen + 1),
                    [])
   
def countPasswords(segList, segOrdList):
   return reduce(add, [reduce(mul, [len(segList[segIndex])
                                    for segIndex in segOrd])
                       for segOrd in segOrdList])

# Generates passwords from segs in segList
#     Example Input: [['a'],['b'],['c'],['1','2'],['!']]
# The segOrdList contains a list of ordered 
# permutations of the segList:
#     Example Input: [[1,2,3],[3,1,2,],[1,2]]
# Yields one password at a time until all permutations are exhausted
#     Example: a1!, a2!, b1!, b2!, c1!, c2!,
#              !a1, !a2, !b1, !b2, !c1, !c2,
#              a1, a2, b1, b2, c1, c2
def paswordGenerator(segList, segOrdList, result = ''):
   for segOrd in segOrdList:
      orderedSegList = [segList[segIndex] for segIndex in segOrd]
      for seg in orderedSegList[0]:
         if len(segList) > 1:
            internalPWGenerator = paswordGenerator(segList[1:], result + seg)
            for item in internalPWGenerator:
               yield item
         else:
            yield result + seg

def searchForPassword(segList, segOrdList=[]):
   if len(segOrdList) == 0:
      segOrdList = [range(len(segList))]
   passwordCount = countPasswords(segList, segOrdList)
   startTime = RightNow()
   found = False
   thePasswordGenerator = paswordGenerator(segList, segOrdList)
   myEncryptedWlt = loadWallet();
   for i,p in enumerate(thePasswordGenerator):
      isValid = myEncryptedWlt.verifyPassphrase( SecureBinaryData(p) ) 
         
      if isValid:
         # If the passphrase was wrong, it would error out, and not continue
         print 'Passphrase found!'
         print ''
         print '\t', p
         print ''
         print 'Thanks for using this script.  If you recovered coins because of it, '
         print 'please consider donating :) '
         print '   1ArmoryXcfq7TnCSuZa9fQjRYwJ4bkRKfv'
         print ''
         found = True
         open('FOUND_PASSWORD.txt','w').write(p)
         break
      elif i%100==0:
            telapsed = (RightNow() - startTime)/3600.
            print ('%d/%d passphrases tested... (%0.1f hours so far)'%(i,passwordCount,telapsed)).rjust(40)
      print p,
      if i % 10 == 9:
         print
   
   if not found:
      print ''
      
      print 'Script finished!'
      print 'Sorry, none of the provided passphrases were correct :('
      print ''

