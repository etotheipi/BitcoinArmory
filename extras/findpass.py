'''
Created on Aug 30, 2013

@author: Andy
'''
from sys import path
import os

from armoryengine import PyBtcWallet
from armoryengine.ArmoryUtils import RightNow
from CppBlockUtils import SecureBinaryData
from operator import add, mul
# Give an upper limit for any method to return
# if the limit is exceded raise MaxResultsExceeded exception
MAX_LIST_LEN = 20000000

class MaxResultsExceeded(Exception): pass
class WalletNotFound(object): pass

path.append('..')
path.append('/usr/bin/armory')

class PwdSeg(object):
   def __init__(self, known):
      self.known = known
   
   # Abstract method
   def getSegListLen(self):
      raise NotImplementedError("Subclass must implement getSegListLength()")

   # Abstract Generator
   def segListGenerator(self, maxResults=MAX_LIST_LEN):
      raise NotImplementedError("Subclass must implement getSegList()")
      yield None
   
   # Abstract method
   def getSegList(self, maxResults=MAX_LIST_LEN):
      raise NotImplementedError("Subclass must implement getSegList()")

class UnknownCaseSeg(PwdSeg):
   def __init__(self, known):
      super(UnknownCaseSeg, self).__init__(known)
   
   getBothCases = lambda self, ch : [ch.lower(), ch.upper()] if ch.lower() != ch.upper() else [ch]
   
   def segListRecursiveGenerator(self, seg):
      if len(seg) > 0:
         for a in self.getBothCases(seg[0]):
            for b in self.segListRecursiveGenerator(seg[1:]):
               yield a + b
      else:
         yield ''
         
   def getSegListLen(self):
      return reduce(mul, [1 if ch.lower() == ch.upper() else 2 for ch in self.known]) 
   
   def segListGenerator(self, maxResults=MAX_LIST_LEN):
      if self.getSegListLen() > maxResults:
         raise MaxResultsExceeded
      for seg in self.segListRecursiveGenerator(self.known):
         yield seg
      
   def getSegList(self, maxResults=MAX_LIST_LEN):
      return [seg for seg in self.segListGenerator(maxResults)] 
   
class KnownSeg(PwdSeg):
   def __init__(self, known):
      super(KnownSeg, self).__init__(known)
   
   def getSegListLen(self):
      return 1

   def segListGenerator(self, maxResults=MAX_LIST_LEN):
      yield self.known

   def getSegList(self, maxResults=MAX_LIST_LEN):
      return [seg for seg in self.segListGenerator()]
   
class UnknownSeg(PwdSeg):
   def __init__(self, known, minLen, maxLen):
      super(UnknownSeg, self).__init__(known)
      self.removeDups()
      self.minLen = minLen
      self.maxLen = maxLen
      
   def removeDups(self):
      self.known = ''.join(set(self.known))
      
   def segListRecursiveGenerator(self, segLen):
      if segLen > 0:
         for a in self.known:
            for b in self.segListRecursiveGenerator(segLen-1):
               yield a + b
      else:
         yield ''

   def getSegListLen(self):
      return reduce(add, [len(self.known) ** i for i in range(self.minLen, self.maxLen + 1)]) 
   
   def segListGenerator(self, maxResults=MAX_LIST_LEN):
      if self.getSegListLen() > maxResults:
         raise MaxResultsExceeded
      for segLen in range(self.minLen, self.maxLen + 1):
         for seg in self.segListRecursiveGenerator(segLen):
            yield seg
   
   def getSegList(self, maxResults=MAX_LIST_LEN):
      return [seg for seg in self.segListGenerator(maxResults)]
   



class PasswordFinder(object): 
   def __init__(self, wallet=None, walletPath=''):
      if wallet != None:
         self.wallet = wallet
      else:
         if not os.path.exists(walletPath):
            print 'Wallet does not exist:'
            print '  ', walletPath
            raise WalletNotFound
         self.wallet = PyBtcWallet().readWalletFile(walletPath)

   def countPasswords(self, segList, segOrdList):
      return reduce(add, [reduce(mul, [len(segList[segIndex])
                                       for segIndex in segOrd])
                          for segOrd in segOrdList])
   
   def recursivePasswordGenerator(self, segList):
      if len(segList) > 0:
         for a in segList[0]:
            for b in self.recursivePasswordGenerator(segList[1:]):
               yield a + b
      else:
         yield ''
         
   # Generates passwords from segs in segList
   #     Example Input: [['a','b','c'],['1','2'],['!']]
   # The segOrdList contains a list of ordered 
   # permutations of the segList:
   #     Example Input: [[0,1,2],[2,0,1,],[0,1]]
   # Yields one password at a time until all permutations are exhausted
   #     Example: a1!, a2!, b1!, b2!, c1!, c2!,
   #              !a1, !a2, !b1, !b2, !c1, !c2,
   #              a1, a2, b1, b2, c1, c2
   # The above example is a test case found in test/FindPassTest.py
   def passwordGenerator(self, segList, segOrdList):
      for segOrd in segOrdList:
         orderedSegList = [segList[segIndex] for segIndex in segOrd]
         for result in self.recursivePasswordGenerator(orderedSegList):
            yield result
   
   def searchForPassword(self, segList, segOrdList=[]):
      if len(segOrdList) == 0:
         segOrdList = [range(len(segList))]
      passwordCount = self.countPasswords(segList, segOrdList)
      startTime = RightNow()
      found = False
      result = None
      for i,p in enumerate(self.passwordGenerator(segList, segOrdList)):
         isValid = self.wallet.verifyPassphrase( SecureBinaryData(p) ) 
            
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
            result = p
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
      return result
'''
if len(argv)<2:
   print '***USAGE: '
   print '    %s /path/to/wallet/file.wallet' % argv[0]
   exit(0)
passwordFinder = PasswordFinder(argv[1])
'''
