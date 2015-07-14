############################################################################
#
# Copyright (C) 2011-2015, Armory Technologies, Inc.
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
############################################################################
#
# Project:    Armory
# Author:     Alan Reiner
# Website:    www.bitcoinarmory.com
# Orig Date:  20 November, 2011
#
############################################################################

import random

from ArmoryUtils import *

class FiniteField(object):
   """
   Create a simple, prime-order FiniteField.  Because this is used only
   to encode data of fixed width, I enforce prime-order by hardcoding
   primes, and you just pick the data width (in bytes).  If your desired
   data width is not here,  simply find a prime number very close to 2^N,
   and add it to the PRIMES map below.

   This will be used for Shamir's Secret Sharing scheme.  Encode your
   data as the coeffient of finite-field polynomial, and store points
   on that polynomial.  The order of the polynomial determines how
   many points are needed to recover the original secret.
   """

   # bytes: primeclosetomaxval
   PRIMES = {   1:  2**8-5,  # mainly for testing
                2:  2**16-39,
                4:  2**32-5,
                8:  2**64-59,
               16:  2**128-797,
               20:  2**160-543,
               24:  2**192-333,
               32:  2**256-357,
               48:  2**384-317,
               64:  2**512-569,
               96:  2**768-825,
              128:  2**1024-105,
              192:  2**1536-3453,
              256:  2**2048-1157  }

   def __init__(self, nbytes):
      if not self.PRIMES.has_key(nbytes):
         LOGERROR('No primes available for size=%d bytes', nbytes)
         self.prime = None
         raise FiniteFieldError
      self.prime = self.PRIMES[nbytes]


   def add(self,a,b):
      return (a+b) % self.prime

   def subtract(self,a,b):
      return (a-b) % self.prime

   def mult(self,a,b):
      return (a*b) % self.prime

   def power(self,a,b):
      result = 1
      while(b>0):
         b,x = divmod(b,2)
         result = (result * (a if x else 1)) % self.prime
         a = a*a % self.prime
      return result

   def powinv(self,a):
      """ USE ONLY PRIME MODULUS """
      return self.power(a,self.prime-2)

   def divide(self,a,b):
      """ USE ONLY PRIME MODULUS """
      baddinv = self.powinv(b)
      return self.mult(a,baddinv)

   def mtrxrmrowcol(self,mtrx,r,c):
      if not len(mtrx) == len(mtrx[0]):
         LOGERROR('Must be a square matrix!')
         return []
      sz = len(mtrx)
      return [[mtrx[i][j] for j in range(sz) if not j==c] for i in range(sz) if not i==r]


   #########################################################################
   def mtrxdet(self,mtrx):
      if len(mtrx)==1:
         return mtrx[0][0]

      if not len(mtrx) == len(mtrx[0]):
         LOGERROR('Must be a square matrix!')
         return -1

      result = 0;
      for i in range(len(mtrx)):
         mult     = mtrx[0][i] * (-1 if i%2==1 else 1)
         subdet   = self.mtrxdet(self.mtrxrmrowcol(mtrx,0,i))
         result   = self.add(result, self.mult(mult,subdet))
      return result

   #########################################################################
   def mtrxmultvect(self,mtrx, vect):
      M,N = len(mtrx), len(mtrx[0])
      if not len(mtrx[0])==len(vect):
         LOGERROR('Mtrx and vect are incompatible: %dx%d, %dx1', M, N, len(vect))
      return [ sum([self.mult(mtrx[i][j],vect[j]) for j in range(N)])%self.prime for i in range(M) ]

   #########################################################################
   def mtrxmult(self,m1, m2):
      M1,N1 = len(m1), len(m1[0])
      M2,N2 = len(m2), len(m2[0])
      if not N1==M2:
         LOGERROR('Mtrx and vect are incompatible: %dx%d, %dx%d', M1,N1, M2,N2)
      inner = lambda i,j: sum([self.mult(m1[i][k],m2[k][j]) for k in range(N1)])
      return [ [inner(i,j)%self.prime for j in range(N1)] for i in range(M1) ]

   #########################################################################
   def mtrxadjoint(self,mtrx):
      sz = len(mtrx)
      inner = lambda i,j: self.mtrxdet(self.mtrxrmrowcol(mtrx,i,j))
      return [[((-1 if (i+j)%2==1 else 1)*inner(j,i))%self.prime for j in range(sz)] for i in range(sz)]

   #########################################################################
   def mtrxinv(self,mtrx):
      det = self.mtrxdet(mtrx)
      adj = self.mtrxadjoint(mtrx)
      sz = len(mtrx)
      return [[self.divide(adj[i][j],det) for j in range(sz)] for i in range(sz)]


############################################################################
def SplitSecret(secret, needed, pieces, nbytes=None, use_random_x=False):
   if isinstance(secret, SecureBinaryData):
      secret = secret.toBinStr()

   if nbytes==None:
      nbytes = len(secret)

   ff = FiniteField(nbytes)
   fragments = []

   # Convert secret to an integer
   a = binary_to_int(SecureBinaryData(secret).toBinStr(),BIGENDIAN)
   if not a<ff.prime:
      LOGERROR('Secret must be less than %s', int_to_hex(ff.prime,endOut=BIGENDIAN))
      LOGERROR('             You entered %s', int_to_hex(a,endOut=BIGENDIAN))
      raise FiniteFieldError

   if not pieces>=needed:
      LOGERROR('You must create more pieces than needed to reconstruct!')
      raise FiniteFieldError

   if needed==1 or needed>8:
      LOGERROR('Can split secrets into parts *requiring* at most 8 fragments')
      LOGERROR('You can break it into as many optional fragments as you want')
      raise FiniteFieldError


   # We deterministically produce the coefficients so that we always use the
   # same polynomial for a given secret
   lasthmac = secret[:]
   othernum = []
   for i in range(pieces+needed-1):
      lasthmac = HMAC512_buggy(lasthmac, 'splitsecrets')[:nbytes]
      othernum.append(binary_to_int(lasthmac))

   def poly(x):
      polyout = ff.mult(a, ff.power(x,needed-1))
      for i,e in enumerate(range(needed-2,-1,-1)):
         term = ff.mult(othernum[i], ff.power(x,e))
         polyout = ff.add(polyout, term)
      return polyout

   for i in range(pieces):
      x = othernum[i+2] if use_random_x else i+1
      fragments.append( [x, poly(x)] )

   secret,a = None,None
   fragments = [ [int_to_binary(p, nbytes, BIGENDIAN) for p in frag] for frag in fragments]
   return fragments


############################################################################
def ReconstructSecret(fragments, needed, nbytes):

   ff = FiniteField(nbytes)
   pairs = fragments[:needed]
   m = []
   v = []
   for x,y in pairs:
      x = binary_to_int(x, BIGENDIAN)
      y = binary_to_int(y, BIGENDIAN)
      m.append([])
      for i,e in enumerate(range(needed-1,-1,-1)):
         m[-1].append( ff.power(x,e) )
      v.append(y)

   minv = ff.mtrxinv(m)
   outvect = ff.mtrxmultvect(minv,v)
   return int_to_binary(outvect[0], nbytes, BIGENDIAN)


############################################################################
def createTestingSubsets( fragIndices, M, maxTestCount=20):
   """
   Returns (IsRandomized, listOfTuplesOfSizeM)
   """
   numIdx = len(fragIndices)

   if M>numIdx:
      LOGERROR('Insufficent number of fragments')
      raise KeyDataError
   elif M==numIdx:
      LOGINFO('Fragments supplied == needed.  One subset to test (%s-of-N)' % M)
      return ( False, [tuple(fragIndices)] )
   else:
      LOGINFO('Test reconstruct %s-of-N, with %s fragments' % (M, numIdx))
      subs = []

      # Compute the number of possible subsets.  This is stable because we
      # shouldn't ever have more than 12 fragments
      fact = math.factorial
      numCombo = fact(numIdx) / ( fact(M) * fact(numIdx-M) )

      if numCombo <= maxTestCount:
         LOGINFO('Testing all %s combinations...' % numCombo)
         for x in xrange(2**numIdx):
            bits = int_to_bitset(x)
            if not bits.count('1') == M:
               continue

            subs.append(tuple([fragIndices[i] for i,b in enumerate(bits)
                               if b=='1']))

         return (False, sorted(subs))
      else:
         LOGINFO('#Subsets > %s, will need to randomize' % maxTestCount)
         usedSubsets = set()
         while len(subs) < maxTestCount:
            sample = tuple(sorted(random.sample(fragIndices, M)))
            if not sample in usedSubsets:
               usedSubsets.add(sample)
               subs.append(sample)

         return (True, sorted(subs))



############################################################################
def testReconstructSecrets(fragMap, M, maxTestCount=20):
   # If fragMap has X elements, then it will test all X-choose-M subsets of
   # the fragMap and return the restored secret for each one.  If there's more
   # subsets than maxTestCount, then just do a random sampling of the possible
   # subsets
   fragKeys = [k for k in fragMap.iterkeys()]
   isRandom, subs = createTestingSubsets(fragKeys, M, maxTestCount)
   nBytes = len(fragMap[fragKeys[0]][1])
   LOGINFO('Testing %d-byte fragments' % nBytes)

   testResults = []
   for subset in subs:
      fragSubset = [fragMap[i][:] for i in subset]

      recon = ReconstructSecret(fragSubset, M, nBytes)
      testResults.append((subset, recon))

   return isRandom, testResults


############################################################################
def ComputeFragIDBase58(M, wltIDBin):
   mBin4   = int_to_binary(M, widthBytes=4, endOut=BIGENDIAN)
   fragBin = hash256(wltIDBin + mBin4)[:4]
   fragB58 = str(M) + binary_to_base58(fragBin)
   return fragB58


############################################################################
def ComputeFragIDLineHex(M, index, wltIDBin, isSecure=False, addSpaces=False):
   fragID  = int_to_hex((128+M) if isSecure else M)
   fragID += int_to_hex(index+1)
   fragID += binary_to_hex(wltIDBin)

   if addSpaces:
      fragID = ' '.join([fragID[i*4:(i+1)*4] for i in range(4)])

   return fragID


############################################################################
def ReadFragIDLineBin(binLine):
   doMask = binary_to_int(binLine[0]) > 127
   M      = binary_to_int(binLine[0]) & 0x7f
   fnum   = binary_to_int(binLine[1])
   wltID  = binLine[2:]

   idBase58 = ComputeFragIDBase58(M, wltID) + '-#' + str(fnum)
   return (M, fnum, wltID, doMask, idBase58)

