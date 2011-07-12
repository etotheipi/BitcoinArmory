#! /usr/bin/env python

################################################################################
# This source copied directly from Lis on the bitcoin forums:
#     http://forum.bitcoin.org/index.php?topic=23241.0
################################################################################

import random

class CurveFp( object ):
   def __init__( self, p, a, b ):
      self.__p = p
      self.__a = a
      self.__b = b

   def p( self ):
      return self.__p

   def a( self ):
      return self.__a

   def b( self ):
      return self.__b

   def contains_point( self, x, y ):
      return ( y * y - ( x * x * x + self.__a * x + self.__b ) ) % self.__p == 0

class Point( object ):
   def __init__( self, curve, x, y, order = None ):
      self.__curve = curve
      self.__x = x
      self.__y = y
      self.__order = order
      if self.__curve: assert self.__curve.contains_point( x, y )
      if order: assert self * order == INFINITY
 
   def __add__( self, other ):
      if other == INFINITY: return self
      if self == INFINITY: return other
      assert self.__curve == other.__curve
      if self.__x == other.__x:
         if ( self.__y + other.__y ) % self.__curve.p() == 0:
            return INFINITY
         else:
            return self.double()

      p = self.__curve.p()
      l = ( ( other.__y - self.__y ) * inverse_mod(other.__x - self.__x, p) ) % p
      x3 = ( l * l - self.__x - other.__x ) % p
      y3 = ( l * ( self.__x - x3 ) - self.__y ) % p
      return Point( self.__curve, x3, y3 )

   def __mul__( self, other ):
      def leftmost_bit( x ):
         assert x > 0
         result = 1L
         while result <= x: result = 2 * result
         return result / 2

      e = other
      if self.__order: e = e % self.__order
      if e == 0: return INFINITY
      if self == INFINITY: return INFINITY
      assert e > 0
      e3 = 3 * e
      negative_self = Point( self.__curve, self.__x, -self.__y, self.__order )
      i = leftmost_bit( e3 ) / 2
      result = self
      while i > 1:
         result = result.double()
         if ( e3 & i ) != 0 and ( e & i ) == 0: result = result + self
         if ( e3 & i ) == 0 and ( e & i ) != 0: result = result + negative_self
         i = i / 2
      return result

   def __rmul__( self, other ):
      return self * other

   def __str__( self ):
      if self == INFINITY: return "infinity"
      return "(%d,%d)" % ( self.__x, self.__y )

   def double( self ):
      if self == INFINITY:
         return INFINITY

      p = self.__curve.p()
      a = self.__curve.a()
      l = ( (3 * self.__x * self.__x + a) * inverse_mod(2 * self.__y, p) ) % p
      x3 = ( l * l - 2 * self.__x ) % p
      y3 = ( l * ( self.__x - x3 ) - self.__y ) % p
      return Point( self.__curve, x3, y3 )

   def x( self ):
      return self.__x

   def y( self ):
      return self.__y

   def curve( self ):
      return self.__curve
   
   def order( self ):
      return self.__order
      
INFINITY = Point( None, None, None )

def inverse_mod( a, m ):
   if a < 0 or m <= a: a = a % m
   c, d = a, m
   uc, vc, ud, vd = 1, 0, 0, 1
   while c != 0:
      q, c, d = divmod( d, c ) + ( c, )
      uc, vc, ud, vd = ud - q*uc, vd - q*vc, uc, vc
   assert d == 1
   if ud > 0: return ud
   else: return ud + m

# secp256k1
_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2FL
_r = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141L
_b = 0x0000000000000000000000000000000000000000000000000000000000000007L
_a = 0x0000000000000000000000000000000000000000000000000000000000000000L
_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798L
_Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8L

class Signature( object ):
   def __init__( self, r, s ):
      self.r = r
      self.s = s
      
class Public_key( object ):
   def __init__( self, generator, point ):
      self.curve = generator.curve()
      self.generator = generator
      self.point = point
      n = generator.order()
      if not n:
         raise RuntimeError, "Generator point must have order."
      if not n * point == INFINITY:
         raise RuntimeError, "Generator point order is bad."
      if point.x() < 0 or n <= point.x() or point.y() < 0 or n <= point.y():
         raise RuntimeError, "Generator point has x or y out of range."

   def verifies( self, hash, signature ):
      G = self.generator
      n = G.order()
      r = signature.r
      s = signature.s
      if r < 1 or r > n-1: return False
      if s < 1 or s > n-1: return False
      c = inverse_mod( s, n )
      u1 = ( hash * c ) % n
      u2 = ( r * c ) % n
      xy = u1 * G + u2 * self.point
      v = xy.x() % n
      return v == r

class Private_key( object ):
   def __init__( self, public_key, secret_multiplier ):
      self.public_key = public_key
      self.secret_multiplier = secret_multiplier

   def der( self ):
      hex_der_key = '06052b8104000a30740201010420' + \
                    '%064x' % self.secret_multiplier + \
                    'a00706052b8104000aa14403420004' + \
                    '%064x' % self.public_key.point.x() + \
                    '%064x' % self.public_key.point.y()
      return hex_der_key.decode('hex')

   def sign( self, hash, random_k ):
      G = self.public_key.generator
      n = G.order()
      k = random_k % n
      p1 = k * G
      r = p1.x()
      if r == 0: raise RuntimeError, "amazingly unlucky random number r"
      s = ( inverse_mod( k, n ) * \
               ( hash + ( self.secret_multiplier * r ) % n ) ) % n
      if s == 0: raise RuntimeError, "amazingly unlucky random number s"
      return Signature( r, s )

curve_256 = CurveFp( _p, _a, _b )
generator_256 = Point( curve_256, _Gx, _Gy, _r )
g = generator_256

if __name__ == "__main__":
   print '======================================================================='
   ### generate privkey
   randrange = random.SystemRandom().randrange
   n = g.order()
   secret = randrange( 1, n )
   ### set privkey
   #secret = 0xC85AFBACCF3E1EE40BDCD721A9AD1341344775D51840EFC0511E0182AE92F78EL
   ### print privkey
   print 'secret', hex(secret)

   
   ### generate pubkey
   pubkey = Public_key( g, g * secret )
   ### set pubkey
   #pubkey = Public_key(g, Point( curve_256, 0x40f9f833a25c725402e242965410b5bb992dc4fea1328681f0a74571c3104e36L,
   #                                         0x0882ea6ae14b6b1316e71e76cc51867cba20cafabd349753058b8c4677be50caL))
   ### print pubkey
   print 'pubkey', hex(pubkey.point.x()), hex(pubkey.point.y())

   privkey = Private_key( pubkey, secret )
   
   # set hash
   #hash = randrange( 1, n )
   hash = 0x0000000000000000000000000000000000000000000000000000000000000000L

   ### make signature on hash
   signature = privkey.sign( hash, randrange( 1, n ) )
   ### set signature
   #signature = Signature(0x0000000000000000000000000000000000000000000000000000000000000000L,
   #                                 0x0000000000000000000000000000000000000000000000000000000000000000L)
                                    
   ### print signature
   print 'signature', hex(signature.r), hex(signature.s)


   #print '======================================================================='
   print 'verifies', pubkey.verifies( hash, signature )
if __name__ == "__main__":
   print '======================================================================='
