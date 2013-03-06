################################################################################
#
# Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################

"""
Shamir's Secret Sharing

This is a completely self-contained python script for "fragmenting" secrets
into multiple pieces, of which any subset is sufficient for recovering the
original secret.  This uses finite fields which are implemented entirely with
python's native big-integer handling (and some creative list comprehensions).

There's nothing fast about this code -- the matrix operations and finite field
operations are intended to be compact, not fast.  As such, it only goes up to
8-of-N secret splitting (no limit on N) before run times start getting totally
prohibitive.  But that should cover a vast majority of use cases for this code
sample.

"""

import hashlib

LITTLEENDIAN  = '<';
BIGENDIAN     = '>';

def sha256(bits):
   return hashlib.new('sha256', bits).digest()
def sha512(bits):
   return hashlib.new('sha512', bits).digest()
def hash256(s):
   """ Double-SHA256 """
   return sha256(sha256(s))
def HMAC(key, msg, hashfunc=sha512):
   """ This is intended to be simple, not fast.  For speed, use HDWalletCrypto() """
   key = (sha512(key) if len(key)>64 else key)
   key = key + ('\x00'*(64-len(key)) if len(key)<64 else '')
   okey = ''.join([chr(ord('\x5c')^ord(c)) for c in key])
   ikey = ''.join([chr(ord('\x36')^ord(c)) for c in key])
   return hashfunc( okey + hashfunc(ikey + msg) )
HMAC512 = lambda key,msg: HMAC(key,msg,sha512)



##### Switch endian-ness #####
def hex_switchEndian(s):
   """ Switches the endianness of a hex string (in pairs of hex chars) """
   pairList = [s[i]+s[i+1] for i in xrange(0,len(s),2)]
   return ''.join(pairList[::-1])

##### INT/HEXSTR #####
def int_to_hex(i, widthBytes=0, endOut=LITTLEENDIAN):
   """
   Convert an integer (int() or long()) to hexadecimal.  Default behavior is
   to use the smallest even number of hex characters necessary, and using
   little-endian.   Use the widthBytes argument to add 0-padding where needed
   if you are expecting constant-length output.
   """
   h = hex(i)[2:]
   if isinstance(i,long):
      h = h[:-1]
   if len(h)%2 == 1:
      h = '0'+h
   if not widthBytes==0:
      nZero = 2*widthBytes - len(h)
      if nZero > 0:
         h = '0'*nZero + h
   if endOut==LITTLEENDIAN:
      h = hex_switchEndian(h)
   return h

def hex_to_int(h, endIn=LITTLEENDIAN):
   """
   Convert hex-string to integer (or long).  Default behavior is to interpret
   hex string as little-endian
   """
   hstr = h[:]  # copies data, no references
   if endIn==LITTLEENDIAN:
      hstr = hex_switchEndian(hstr)
   return( int(hstr, 16) )


##### HEXSTR/BINARYSTR #####
def hex_to_binary(h, endIn=LITTLEENDIAN, endOut=LITTLEENDIAN):
   """
   Converts hexadecimal to binary (in a python string).  Endianness is
   only switched if (endIn != endOut)
   """
   bout = h[:]  # copies data, no references
   if not endIn==endOut:
      bout = hex_switchEndian(bout)
   return bout.decode('hex_codec')


def binary_to_hex(b, endOut=LITTLEENDIAN, endIn=LITTLEENDIAN):
   """
   Converts binary to hexadecimal.  Endianness is only switched
   if (endIn != endOut)
   """
   hout = b.encode('hex_codec')
   if not endOut==endIn:
      hout = hex_switchEndian(hout)
   return hout


##### INT/BINARYSTR #####
def int_to_binary(i, widthBytes=0, endOut=LITTLEENDIAN):
   """
   Convert integer to binary.  Default behavior is use as few bytes
   as necessary, and to use little-endian.  This can be changed with
   the two optional input arguemnts.
   """
   h = int_to_hex(i,widthBytes)
   return hex_to_binary(h, endOut=endOut)

def binary_to_int(b, endIn=LITTLEENDIAN):
   """
   Converts binary to integer (or long).  Interpret as LE by default
   """
   h = binary_to_hex(b, endIn, LITTLEENDIAN)
   return hex_to_int(h)


################################################################################
# Convert regular hex into an easily-typed Base16
NORMALCHARS  = '0123 4567 89ab cdef'.replace(' ','')
EASY16CHARS  = 'asdf ghjk wert uion'.replace(' ','')
hex_to_base16_map = {}
base16_to_hex_map = {}
for n,b in zip(NORMALCHARS,EASY16CHARS):
   hex_to_base16_map[n] = b
   base16_to_hex_map[b] = n

def binary_to_easyType16(binstr):
   return ''.join([hex_to_base16_map[c] for c in binary_to_hex(binstr)])

def easyType16_to_binary(b16str):
   return hex_to_binary(''.join([base16_to_hex_map[c] for c in b16str]))


def makeSixteenBytesEasy(b16):
   if not len(b16)==16:
      raise ValueError, 'Must supply 16-byte input'
   chk2 = computeChecksum(b16, nBytes=2)
   et18 = binary_to_easyType16(b16 + chk2) 
   return ' '.join([et18[i*4:(i+1)*4] for i in range(9)])

def readSixteenEasyBytes(et18):
   b18 = easyType16_to_binary(et18.strip().replace(' ',''))
   b16 = b18[:16]
   chk = b18[ 16:]
   b16new = verifyChecksum(b16, chk)
   if len(b16new)==0:
      return ('','Error_2+')
   elif not b16new==b16:
      return (b16new,'Fixed_1')
   else:
      return (b16new,None)

def computeChecksum(binaryStr, nBytes=4, hashFunc=hash256):
   return hashFunc(binaryStr)[:nBytes]

def verifyChecksum(binaryStr, chksum, hashFunc=hash256, fixIfNecessary=True, \
                                                              beQuiet=False):
   bin1 = str(binaryStr)
   bin2 = binary_switchEndian(binaryStr)


   if hashFunc(bin1).startswith(chksum):
      return bin1
   elif hashFunc(bin2).startswith(chksum):
      if not beQuiet: LOGWARN( '***Checksum valid for input with reversed endianness')
      if fixIfNecessary:
         return bin2
   elif fixIfNecessary:
      if not beQuiet: LOGWARN('***Checksum error!  Attempting to fix...'),
      fixStr = fixChecksumError(bin1, chksum, hashFunc)
      if len(fixStr)>0:
         if not beQuiet: LOGWARN('fixed!')
         return fixStr
      else:
         # ONE LAST CHECK SPECIFIC TO MY SERIALIZATION SCHEME:
         # If the string was originally all zeros, chksum is hash256('')
         # ...which is a known value, and frequently used in my files
         if chksum==hex_to_binary('5df6e0e2'):
            if not beQuiet: LOGWARN('fixed!')
            return ''

   # ID a checksum byte error...
   origHash = hashFunc(bin1)
   for i in range(len(chksum)):
      chkArray = [chksum[j] for j in range(len(chksum))]
      for ch in range(256):
         chkArray[i] = chr(ch)
         if origHash.startswith(''.join(chkArray)):
            LOGWARN('***Checksum error!  Incorrect byte in checksum!')
            return bin1

   LOGWARN('Checksum fix failed')
   return ''



# START FINITE FIELD OPERATIONS
class FiniteFieldError(Exception): pass

###################################################################################
class FiniteField(object):
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

   def add(self,a,b): return (a+b) % self.prime
   def subtract(self,a,b): return (a-b) % self.prime
   def mult(self,a,b): return (a*b) % self.prime
   
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
   
   ################################################################################
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
     
   ################################################################################
   def mtrxmultvect(self,mtrx, vect):
      M,N = len(mtrx), len(mtrx[0])
      if not len(mtrx[0])==len(vect):
         LOGERROR('Mtrx and vect are incompatible: %dx%d, %dx1', M, N, len(vect))
      return [ sum([self.mult(mtrx[i][j],vect[j]) for j in range(N)])%self.prime for i in range(M) ]
   
   ################################################################################
   def mtrxmult(self,m1, m2):
      M1,N1 = len(m1), len(m1[0])
      M2,N2 = len(m2), len(m2[0])
      if not N1==M2:
         LOGERROR('Mtrx and vect are incompatible: %dx%d, %dx%d', M1,N1, M2,N2)
      inner = lambda i,j: sum([self.mult(m1[i][k],m2[k][j]) for k in range(N1)])
      return [ [inner(i,j)%self.prime for j in range(N1)] for i in range(M1) ]
   
   ################################################################################
   def mtrxadjoint(self,mtrx):
      sz = len(mtrx)
      inner = lambda i,j: self.mtrxdet(self.mtrxrmrowcol(mtrx,i,j))
      return [[((-1 if (i+j)%2==1 else 1)*inner(j,i))%self.prime for j in range(sz)] for i in range(sz)]
      
   ################################################################################
   def mtrxinv(self,mtrx):
      det = self.mtrxdet(mtrx)
      adj = self.mtrxadjoint(mtrx)
      sz = len(mtrx)
      return [[self.divide(adj[i][j],det) for j in range(sz)] for i in range(sz)]

###################################################################################
def SplitSecret(secret, needed, pieces, nbytes=None):
   if nbytes==None:
      nbytes = len(secret)

   ff = FiniteField(nbytes)
   fragments = []

   # Convert secret to an integer
   a = binary_to_int(secret,BIGENDIAN)
   if not a<ff.prime:
      LOGERROR('Secret must be less than %s', int_to_hex(ff.prime,BIGENDIAN))
      LOGERROR('             You entered %s', int_to_hex(a,BIGENDIAN))
      raise FiniteFieldError

   if not pieces>=needed:
      LOGERROR('You must create more pieces than needed to reconstruct!')
      raise FiniteFieldError


   if needed==1 or needed>8:
      LOGERROR('Can split secrets into parts *requiring* at most 8 fragments')
      LOGERROR('You can break it into as many optional fragments as you want')
      return fragments


   lasthmac = secret[:]
   othernum = []
   for i in range(pieces+needed-1):
      lasthmac = HMAC512(lasthmac, 'splitsecrets')[:nbytes]
      othernum.append(lasthmac)

   othernum = [binary_to_int(n) for n in othernum]
   if needed==2:
      b = othernum[0]
      poly = lambda x:  ff.add(ff.mult(a,x), b)
      for i in range(pieces):
         x = othernum[i+1]
         fragments.append( [x, poly(x)] )

   elif needed==3:
      def poly(x):
         b = othernum[0]
         c = othernum[1]
         x2  = ff.power(x,2)
         ax2 = ff.mult(a,x2)
         bx  = ff.mult(b,x)
         return ff.add(ff.add(ax2,bx),c) 

      for i in range(pieces):
         x = othernum[i+2]
         fragments.append( [x, poly(x)] )

   else:
      def poly(x):
         polyout = ff.mult(a, ff.power(x,needed-1))
         for i,e in enumerate(range(needed-2,-1,-1)):
            term = ff.mult(othernum[i], ff.power(x,e))
            polyout = ff.add(polyout, term)
         return polyout
         
      for i in range(pieces):
         x = othernum[i+2]
         fragments.append( [x, poly(x)] )


   a = None
   fragments = [ [int_to_binary(p, nbytes, BIGENDIAN) for p in frag] for frag in fragments]
   return fragments


################################################################################
def ReconstructSecret(fragments, needed, nbytes):

   ff = FiniteField(nbytes)
   if needed==2:
      x1,y1 = [binary_to_int(f, BIGENDIAN) for f in fragments[0]]
      x2,y2 = [binary_to_int(f, BIGENDIAN) for f in fragments[1]]

      m = [[x1,1],[x2,1]]
      v = [y1,y2]

      minv = ff.mtrxinv(m)
      a,b = ff.mtrxmultvect(minv,v)
      return int_to_binary(a, nbytes, BIGENDIAN)
   
   elif needed==3:
      x1,y1 = [binary_to_int(f, BIGENDIAN) for f in fragments[0]]
      x2,y2 = [binary_to_int(f, BIGENDIAN) for f in fragments[1]]
      x3,y3 = [binary_to_int(f, BIGENDIAN) for f in fragments[2]]

      sq = lambda x: ff.power(x,2)
      m = [  [sq(x1), x1 ,1], \
             [sq(x2), x2, 1], \
             [sq(x3), x3, 1] ]
      v = [y1,y2,y3]

      minv = ff.mtrxinv(m)
      a,b,c = ff.mtrxmultvect(minv,v)
      return int_to_binary(a, nbytes, BIGENDIAN)
   else:
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
         
   


if __name__=="__main__":
   import random
   # Create and fragment a 16-byte secret
   nBytes = 16
   secret = '9f'*nBytes
   secbin = hex_to_binary(secret)
   
   need = 4;
   pcs = SplitSecret(secbin, need, 10);  # Create 10 pieces, any 4 needed (4-of-10)

   print 'Original Secret: %s' % secret
   print 'Fragmenting into 4-of-10 pieces'
   print 'Printing fragments:'
   for i,xy in enumerate(pcs):
      x,y = [binary_to_hex(z) for z in xy]
      print '   Fragment %d: (x,y) = (%s, %s)' % (i,x,y)


   decorated = [(i,z[0],z[1]) for i,z in enumerate(pcs)]
   print 'Testing reconstruction from various subsets:'
   
   for test in range(10):
      indices,xys = [0]*need, [[0,0] for i in range(need)]
      random.shuffle(decorated)
      
      for j in range(need):
         indices[j], xys[j][0], xys[j][1]= decorated[j]
      
      print ('   Using fragments (%d,%d,%d,%d)' % tuple(sorted(indices))),
      sec = ReconstructSecret(xys, need, nBytes)
      print ' Reconstructed secret: %s' % binary_to_hex(sec)




